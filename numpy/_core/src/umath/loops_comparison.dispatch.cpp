#include "numpy/npy_common.h"

#include "loops.h"
#include "loops_utils.h"

#include "common.hpp"
#include "simd/simd.hpp"

namespace {
using namespace np::simd;

template <typename T>
struct OpEq {
#if NPY_SIMD
    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Vec<T> operator()(const Vec<T_> &a)
    { return a; }

    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE auto operator()(const Vec<T_> &a, const Vec<T_> &b)
    {return Eq(a, b); }
#endif
    NPY_FINLINE T operator()(T a)
    { return a; }

    NPY_FINLINE npy_bool operator()(T a, T b)
    { return a == b; }
};

template <typename T>
struct OpNe {
#if NPY_SIMD
    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Vec<T> operator()(const Vec<T_> &a)
    { return a; }

    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE auto operator()(const Vec<T_> &a, const Vec<T_> &b)
    { return Ne(a, b); }
#endif
    NPY_FINLINE T operator()(T a)
    { return a; }

    NPY_FINLINE npy_bool operator()(T a, T b)
    { return a != b; }
};

template <typename T>
struct OpLt {
#if NPY_SIMD
    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Vec<T> operator()(const Vec<T_> &a)
    { return a; }

    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE auto operator()(const Vec<T_> &a, const Vec<T_> &b)
    { return Lt(a, b); }
#endif
    NPY_FINLINE T operator()(T a)
    { return a; }

    NPY_FINLINE npy_bool operator()(T a, T b)
    { return a < b; }
};

template <typename T>
struct OpLe {
#if NPY_SIMD
    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Vec<T> operator()(const Vec<T_> &a)
    { return a; }

    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE auto operator()(const Vec<T_> &a, const Vec<T_> &b)
    { return Le(a, b); }
#endif
    NPY_FINLINE T operator()(T a)
    { return a; }

    NPY_FINLINE npy_bool operator()(T a, T b)
    { return a <= b; }
};
// as tags only
template <typename T>
struct OpGt {};
template <typename T>
struct OpGe {};

template <typename T>
struct OpEqBool {
#if NPY_SIMD
    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Mask<T> operator()(const Vec<T_> &a)
    {
        const auto zero = Zero<T>();
        return Eq(a, zero);
    }

    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Mask<T> operator()(const Mask<T_> &a, const Mask<T_> &b)
    { return Xnor(a, b); }
#endif
    NPY_FINLINE bool operator()(T v)
    { return v != 0; }

    NPY_FINLINE npy_bool operator()(bool a, bool b)
    { return a == b; }
};

template <typename T>
struct OpNeBool {
#if NPY_SIMD
    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Mask<T> operator()(const Vec<T_> &v)
    {
        const auto zero = Zero<T>();
        return Eq(v, zero);
    }

    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Mask<T> operator()(const Mask<T_> &a, const Mask<T_> &b)
    { return Xor(a, b); }
#endif
    NPY_FINLINE bool operator()(T v)
    { return v != 0; }

    NPY_FINLINE npy_bool operator()(bool a, bool b)
    {
        return a != b;
    }
};

template <typename T>
struct OpLtBool {
#if NPY_SIMD
    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Mask<T> operator()(const Vec<T_> &v)
    {
        const auto zero = Zero<T>();
        return Eq(v, zero);
    }

    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Mask<T> operator()(const Mask<T_> &a, const Mask<T_> &b)
    { return Andc(a, b); }
#endif
    NPY_FINLINE bool operator()(T v)
    { return v != 0; }

    NPY_FINLINE npy_bool operator()(bool a, bool b)
    { return a < b; }
};

template <typename T>
struct OpLeBool {
#if NPY_SIMD
    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Mask<T> operator()(const Vec<T_> &v)
    {
        const auto zero = Zero<T>();
        return Eq(v, zero);
    }

    template <typename T_ = std::enable_if<kSupportLane<T>, T>>
    NPY_FINLINE Mask<T> operator()(const Mask<T_> &a, const Mask<T_> &b)
    { return Orc(a, b); }
#endif
    NPY_FINLINE bool operator()(T v)
    { return v != 0; }

    NPY_FINLINE npy_bool operator()(bool a, bool b)
    { return a <= b; }
};

// as tags only
template <typename T=uint8_t>
struct OpGtBool {};
template <typename T=uint8_t>
struct OpGeBool {};

template <typename T, typename OP>
inline void binary(char **args, size_t len)
{
    OP op;
    const T *src1 = reinterpret_cast<T*>(args[0]);
    const T *src2 = reinterpret_cast<T*>(args[1]);
    npy_bool *dst  = reinterpret_cast<npy_bool*>(args[2]);
#if NPY_SIMD
    if constexpr (kSupportLane<T> && sizeof(npy_bool) == sizeof(uint8_t)) {
        const size_t vstep = NLanes<uint8_t>();
        const size_t nlanes = NLanes<T>();
        const auto truemask = Set(uint8_t(1));
        auto ret = Undef<uint8_t>();

        for (; len >= vstep; len -= vstep, src1 += vstep, src2 += vstep, dst += vstep) {
            auto a1 = op(Load(src1 + nlanes * 0));
            auto b1 = op(Load(src2 + nlanes * 0));
            auto m1 = op(a1, b1);
            if constexpr (sizeof(T) >= 2) {
                auto a2 = op(Load(src1 + nlanes * 1));
                auto b2 = op(Load(src2 + nlanes * 1));
                auto m2 = op(a2, b2);
                if constexpr (sizeof(T) >= 4) {
                    auto a3 = op(Load(src1 + nlanes * 2));
                    auto b3 = op(Load(src2 + nlanes * 2));
                    auto a4 = op(Load(src1 + nlanes * 3));
                    auto b4 = op(Load(src2 + nlanes * 3));
                    auto m3 = op(a3, b3);
                    auto m4 = op(a4, b4);
                    if constexpr (sizeof(T) == 8) {
                        auto a5 = op(Load(src1 + nlanes * 4));
                        auto b5 = op(Load(src2 + nlanes * 4));
                        auto a6 = op(Load(src1 + nlanes * 5));
                        auto b6 = op(Load(src2 + nlanes * 5));
                        auto a7 = op(Load(src1 + nlanes * 6));
                        auto b7 = op(Load(src2 + nlanes * 6));
                        auto a8 = op(Load(src1 + nlanes * 7));
                        auto b8 = op(Load(src2 + nlanes * 7));
                        auto m5 = op(a5, b5);
                        auto m6 = op(a6, b6);
                        auto m7 = op(a7, b7);
                        auto m8 = op(a8, b8);
                        ret = ToVec<uint8_t>(Pack(m1, m2, m3, m4, m5, m6, m7, m8));
                    }
                    else {
                        ret = ToVec<uint8_t>(Pack(m1, m2, m3, m4));
                    }
                }
                else {
                    ret = ToVec<uint8_t>(Pack<uint16_t>(m1, m2));
                }
            }
            else {
                ret = ToVec<uint8_t>(m1);
            }
            Store(reinterpret_cast<uint8_t*>(dst), And(ret, truemask));
        }
        Cleanup();
    }
#endif
    for (; len > 0; --len, ++src1, ++src2, ++dst) {
        const auto a = op(*src1);
        const auto b = op(*src2);
        *dst = op(a, b);
    }
}

template <typename T, typename OP>
inline void binary_scalar1(char **args, size_t len)
{
    OP op;
    const T *src1 = reinterpret_cast<T*>(args[0]);
    const T *src2 = reinterpret_cast<T*>(args[1]);
    npy_bool *dst  = reinterpret_cast<npy_bool*>(args[2]);
#if NPY_SIMD
    if constexpr (kSupportLane<T> && sizeof(npy_bool) == sizeof(uint8_t)) {
        const size_t vstep = NLanes<uint8_t>();
        const size_t nlanes = NLanes<T>();
        const auto truemask = Set(uint8_t(1));
        const auto a1  = op(Set(*src1));
        auto ret = Undef<uint8_t>();

        for (; len >= vstep; len -= vstep, src2 += vstep, dst += vstep) {
            auto b1 = op(Load(src2 + nlanes * 0));
            auto m1 = op(a1, b1);
            if constexpr (sizeof(T) >= 2) {
                auto b2 = op(Load(src2 + nlanes * 1));
                auto m2 = op(a1, b2);
                if constexpr (sizeof(T) >= 4) {
                    auto b3 = op(Load(src2 + nlanes * 2));
                    auto b4 = op(Load(src2 + nlanes * 3));
                    auto m3 = op(a1, b3);
                    auto m4 = op(a1, b4);
                    if constexpr (sizeof(T) == 8) {
                        auto b5 = op(Load(src2 + nlanes * 4));
                        auto b6 = op(Load(src2 + nlanes * 5));
                        auto b7 = op(Load(src2 + nlanes * 6));
                        auto b8 = op(Load(src2 + nlanes * 7));
                        auto m5 = op(a1, b5);
                        auto m6 = op(a1, b6);
                        auto m7 = op(a1, b7);
                        auto m8 = op(a1, b8);
                        ret = ToVec<uint8_t>(Pack(m1, m2, m3, m4, m5, m6, m7, m8));
                    }
                    else {
                        ret = ToVec<uint8_t>(Pack(m1, m2, m3, m4));
                    }
                }
                else {
                    ret = ToVec<uint8_t>(Pack<uint16_t>(m1, m2));
                }
            }
            else {
                ret = ToVec<uint8_t>(m1);
            }
            Store(reinterpret_cast<uint8_t*>(dst), And(ret, truemask));
        }
        Cleanup();
    }
#endif
    const auto a = op(*src1);
    for (; len > 0; --len, ++src2, ++dst) {
        const auto b = op(*src2);
        *dst = op(a, b);
    }
}

template <typename T, typename OP>
inline void binary_scalar2(char **args, size_t len)
{
    OP op;
    const T *src1 = reinterpret_cast<T*>(args[0]);
    const T *src2 = reinterpret_cast<T*>(args[1]);
    npy_bool *dst  = reinterpret_cast<npy_bool*>(args[2]);
#if NPY_SIMD
    if constexpr (kSupportLane<T> && sizeof(npy_bool) == sizeof(uint8_t)) {
        const size_t vstep = NLanes<uint8_t>();
        const size_t nlanes = NLanes<T>();
        const auto truemask = Set(uint8_t(1));
        const auto b1  = op(Set(*src2));
        auto ret = Undef<uint8_t>();

        for (; len >= vstep; len -= vstep, src1 += vstep, dst += vstep) {
            auto a1 = op(Load(src1 + nlanes * 0));
            auto m1 = op(a1, b1);
            if constexpr (sizeof(T) >= 2) {
                auto a2 = op(Load(src1 + nlanes * 1));
                auto m2 = op(a2, b1);
                if constexpr (sizeof(T) >= 4) {
                    auto a3 = op(Load(src1 + nlanes * 2));
                    auto a4 = op(Load(src1 + nlanes * 3));
                    auto m3 = op(a3, b1);
                    auto m4 = op(a4, b1);
                    if constexpr (sizeof(T) == 8) {
                        auto a5 = op(Load(src1 + nlanes * 4));
                        auto a6 = op(Load(src1 + nlanes * 5));
                        auto a7 = op(Load(src1 + nlanes * 6));
                        auto a8 = op(Load(src1 + nlanes * 7));
                        auto m5 = op(a5, b1);
                        auto m6 = op(a6, b1);
                        auto m7 = op(a7, b1);
                        auto m8 = op(a8, b1);
                        ret = ToVec<uint8_t>(Pack(m1, m2, m3, m4, m5, m6, m7, m8));
                    }
                    else {
                        ret = ToVec<uint8_t>(Pack(m1, m2, m3, m4));
                    }
                }
                else {
                    ret = ToVec<uint8_t>(Pack<uint16_t>(m1, m2));
                }
            }
            else {
                ret = ToVec<uint8_t>(m1);
            }
            Store(reinterpret_cast<uint8_t*>(dst), And(ret, truemask));
        }
        Cleanup();
    }
#endif
    const auto b = op(*src2);
    for (; len > 0; --len, ++src1, ++dst) {
        const auto a = op(*src1);
        *dst = op(a, b);
    }
}

template <typename T, typename OP>
static void cmp_binary_branch(char **args, npy_intp const *dimensions, npy_intp const *steps)
{
    char *ip1 = args[0], *ip2 = args[1], *op1 = args[2];
    npy_intp is1 = steps[0], is2 = steps[1], os1 = steps[2];
    npy_intp n = dimensions[0];

    if (!is_mem_overlap(ip1, is1, op1, os1, n) &&
        !is_mem_overlap(ip2, is2, op1, os1, n)
    ) {
        assert(n >= 0);
        size_t len = static_cast<size_t>(n);
        // argument one scalar
        if (is1 == 0 && is2 == sizeof(T) && os1 == sizeof(npy_bool)) {
            binary_scalar1<T, OP>(args, len);
            return;
        }
        // argument two scalar
        if ((is1 == sizeof(T) && is2 == 0 && os1 == sizeof(npy_bool))) {
            binary_scalar2<T, OP>(args, len);
            return;
        }
        if (is1 == sizeof(T) && is2 == sizeof(T) && os1 == sizeof(npy_bool)) {
            binary<T, OP>(args, len);
            return;
        }
    }

    OP op;
    for (npy_intp i = 0; i < n; i++, ip1 += is1, ip2 += is2, op1 += os1) {
        const auto a = op(reinterpret_cast<const T*>(ip1)[0]);
        const auto b = op(reinterpret_cast<const T*>(ip2)[0]);
        reinterpret_cast<npy_bool*>(op1)[0] = op(a, b);
    }
}

template <typename T, template<typename> typename OP>
inline void cmp_binary(char **args, npy_intp const *dimensions, npy_intp const *steps)
{
    /*
     * In order to reduce the size of the binary generated from this source, the
     * following rules are applied: 1) each data type implements its function
     * 'greater' as a call to the function 'less' but with the arguments swapped,
     * the same applies to the function 'greater_equal', which is implemented
     * with a call to the function 'less_equal', and 2) for the integer datatypes
     * of the same size (eg 8-bit), a single kernel of the functions 'equal' and
     * 'not_equal' is used to implement both signed and unsigned types.
     */
    constexpr bool kSwapToUnsigned_ = std::is_integral_v<T> && (
        std::is_same_v<OP<T>, OpEq<T>> ||
        std::is_same_v<OP<T>, OpNe<T>>
    );
    using SwapUnsigned_ = std::make_unsigned_t<
        std::conditional_t<kSwapToUnsigned_, T, int>
    >;
    using TLane_ = std::conditional_t<kSwapToUnsigned_, SwapUnsigned_, T>;
    using TLaneFixed_ = typename np::meta::FixedWidth<TLane_>::Type;

    using TOperation_ = OP<TLaneFixed_>;
    using SwapOperationGt_ = std::conditional_t<
        std::is_same_v<TOperation_, OpGt<TLaneFixed_>>,
        OpLt<TLaneFixed_>, TOperation_
    >;
    using SwapOperationGe_ = std::conditional_t<
        std::is_same_v<TOperation_, OpGe<TLaneFixed_>>,
        OpLe<TLaneFixed_>, SwapOperationGt_
    >;
    using SwapOperationGtBool_ = std::conditional_t<
        std::is_same_v<TOperation_, OpGtBool<TLaneFixed_>>,
        OpLtBool<TLaneFixed_>, SwapOperationGe_
    >;
    using SwapOperation_ = std::conditional_t<
        std::is_same_v<TOperation_, OpGeBool<TLaneFixed_>>,
        OpLeBool<TLaneFixed_>, SwapOperationGtBool_
    >;

    if constexpr (std::is_same_v<SwapOperation_, TOperation_>) {
        cmp_binary_branch<TLaneFixed_, SwapOperation_>(args, dimensions, steps);
    }
    else {
        char *nargs[] = {args[1], args[0], args[2]};
        npy_intp nsteps[] = {steps[1], steps[0], steps[2]};
        cmp_binary_branch<TLaneFixed_, SwapOperation_>(nargs, dimensions, nsteps);
    }

    if constexpr (std::is_same_v<T, npy_float> ||
                  std::is_same_v<T, npy_double>) {
        // clear any FP exceptions
        np::FloatStatus();
    }
}
} // namespace anonymous


/********************************************************************************
 ** Defining ufunc inner functions
 ********************************************************************************/
#define UMATH_IMPL_CMP_UFUNC(TYPE, NAME, T, OP)                                          \
    void NPY_CPU_DISPATCH_CURFX(TYPE##_##NAME)(char **args, npy_intp const *dimensions,  \
                                               npy_intp const *steps, void*)             \
    {                                                                                    \
        cmp_binary<T, OP>(args, dimensions, steps);                                      \
    }

#define UMATH_IMPL_CMP_UFUNC_TYPES(NAME, OP, BOOL_OP)         \
    UMATH_IMPL_CMP_UFUNC(BOOL, NAME, npy_bool, BOOL_OP)       \
    UMATH_IMPL_CMP_UFUNC(UBYTE, NAME, npy_ubyte, OP)          \
    UMATH_IMPL_CMP_UFUNC(BYTE, NAME, npy_byte, OP)            \
    UMATH_IMPL_CMP_UFUNC(USHORT, NAME, npy_ushort, OP)        \
    UMATH_IMPL_CMP_UFUNC(SHORT, NAME, npy_short, OP)          \
    UMATH_IMPL_CMP_UFUNC(UINT, NAME, npy_uint, OP)            \
    UMATH_IMPL_CMP_UFUNC(INT, NAME, npy_int, OP)              \
    UMATH_IMPL_CMP_UFUNC(ULONG, NAME, npy_ulong, OP)          \
    UMATH_IMPL_CMP_UFUNC(LONG, NAME, npy_long, OP)            \
    UMATH_IMPL_CMP_UFUNC(ULONGLONG, NAME, npy_ulonglong, OP)  \
    UMATH_IMPL_CMP_UFUNC(LONGLONG, NAME, npy_longlong, OP)    \
    UMATH_IMPL_CMP_UFUNC(FLOAT, NAME, npy_float, OP)          \
    UMATH_IMPL_CMP_UFUNC(DOUBLE, NAME, npy_double, OP)

UMATH_IMPL_CMP_UFUNC_TYPES(equal, OpEq, OpEqBool)
UMATH_IMPL_CMP_UFUNC_TYPES(not_equal, OpNe, OpNeBool)
UMATH_IMPL_CMP_UFUNC_TYPES(less, OpLt, OpLtBool)
UMATH_IMPL_CMP_UFUNC_TYPES(less_equal, OpLe, OpLeBool)
UMATH_IMPL_CMP_UFUNC_TYPES(greater, OpGt, OpGtBool)
UMATH_IMPL_CMP_UFUNC_TYPES(greater_equal, OpGe, OpGeBool)

