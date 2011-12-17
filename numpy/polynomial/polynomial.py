"""
Objects for dealing with polynomials.

This module provides a number of objects (mostly functions) useful for
dealing with polynomials, including a `Polynomial` class that
encapsulates the usual arithmetic operations.  (General information
on how this module represents and works with polynomial objects is in
the docstring for its "parent" sub-package, `numpy.polynomial`).

Constants
---------
- `polydomain` -- Polynomial default domain, [-1,1].
- `polyzero` -- (Coefficients of the) "zero polynomial."
- `polyone` -- (Coefficients of the) constant polynomial 1.
- `polyx` -- (Coefficients of the) identity map polynomial, ``f(x) = x``.

Arithmetic
----------
- `polyadd` -- add two polynomials.
- `polysub` -- subtract one polynomial from another.
- `polymul` -- multiply two polynomials.
- `polydiv` -- divide one polynomial by another.
- `polypow` -- raise a polynomial to an positive integer power
- `polyval` -- evaluate a polynomial at given points.
- `polyval2d` -- evaluate a 2D polynomial at given points.
- `polyval3d` -- evaluate a 3D polynomial at given points.
- `polygrid2d` -- evaluate a 2D polynomial on a Cartesian product.
- `polygrid3d` -- evaluate a 3D polynomial on a Cartesian product.

Calculus
--------
- `polyder` -- differentiate a polynomial.
- `polyint` -- integrate a polynomial.

Misc Functions
--------------
- `polyfromroots` -- create a polynomial with specified roots.
- `polyroots` -- find the roots of a polynomial.
- `polyvander` -- Vandermonde-like matrix for powers.
- `polyvander2d` -- Vandermonde-like matrix for 2D power series.
- `polyvander3d` -- Vandermonde-like matrix for 3D power series.
- `polyfit` -- least-squares fit returning a polynomial.
- `polytrim` -- trim leading coefficients from a polynomial.
- `polyline` -- polynomial representing given straight line.

Classes
-------
- `Polynomial` -- polynomial class.

See also
--------
`numpy.polynomial`

"""
from __future__ import division

__all__ = ['polyzero', 'polyone', 'polyx', 'polydomain', 'polyline',
    'polyadd', 'polysub', 'polymulx', 'polymul', 'polydiv', 'polypow',
    'polyval', 'polyder', 'polyint', 'polyfromroots', 'polyvander',
    'polyfit', 'polytrim', 'polyroots', 'Polynomial','polyval2d',
    'polyval3d', 'polygrid2d', 'polygrid3d', 'polyvander2d','polyvander3d']

import numpy as np
import numpy.linalg as la
import polyutils as pu
import warnings
from polytemplate import polytemplate

polytrim = pu.trimcoef

#
# These are constant arrays are of integer type so as to be compatible
# with the widest range of other types, such as Decimal.
#

# Polynomial default domain.
polydomain = np.array([-1,1])

# Polynomial coefficients representing zero.
polyzero = np.array([0])

# Polynomial coefficients representing one.
polyone = np.array([1])

# Polynomial coefficients representing the identity x.
polyx = np.array([0,1])

#
# Polynomial series functions
#


def polyline(off, scl) :
    """
    Returns an array representing a linear polynomial.

    Parameters
    ----------
    off, scl : scalars
        The "y-intercept" and "slope" of the line, respectively.

    Returns
    -------
    y : ndarray
        This module's representation of the linear polynomial ``off +
        scl*x``.

    See Also
    --------
    chebline

    Examples
    --------
    >>> from numpy import polynomial as P
    >>> P.polyline(1,-1)
    array([ 1, -1])
    >>> P.polyval(1, P.polyline(1,-1)) # should be 0
    0.0

    """
    if scl != 0 :
        return np.array([off,scl])
    else :
        return np.array([off])


def polyfromroots(roots) :
    """
    Generate a polynomial with the given roots.

    Return the array of coefficients for the polynomial whose leading
    coefficient (i.e., that of the highest order term) is `1` and whose
    roots (a.k.a. "zeros") are given by *roots*.  The returned array of
    coefficients is ordered from lowest order term to highest, and zeros
    of multiplicity greater than one must be included in *roots* a number
    of times equal to their multiplicity (e.g., if `2` is a root of
    multiplicity three, then [2,2,2] must be in *roots*).

    Parameters
    ----------
    roots : array_like
        Sequence containing the roots.

    Returns
    -------
    out : ndarray
        1-d array of the polynomial's coefficients, ordered from low to
        high.  If all roots are real, ``out.dtype`` is a float type;
        otherwise, ``out.dtype`` is a complex type, even if all the
        coefficients in the result are real (see Examples below).

    See Also
    --------
    chebfromroots

    Notes
    -----
    What is returned are the :math:`a_i` such that:

    .. math::

        \\sum_{i=0}^{n} a_ix^i = \\prod_{i=0}^{n} (x - roots[i])

    where ``n == len(roots)``; note that this implies that `1` is always
    returned for :math:`a_n`.

    Examples
    --------
    >>> import numpy.polynomial as P
    >>> P.polyfromroots((-1,0,1)) # x(x - 1)(x + 1) = x^3 - x
    array([ 0., -1.,  0.,  1.])
    >>> j = complex(0,1)
    >>> P.polyfromroots((-j,j)) # complex returned, though values are real
    array([ 1.+0.j,  0.+0.j,  1.+0.j])

    """
    if len(roots) == 0 :
        return np.ones(1)
    else :
        [roots] = pu.as_series([roots], trim=False)
        prd = np.array([1], dtype=roots.dtype)
        for r in roots:
            prd = polysub(polymulx(prd), r*prd)
        return prd


def polyadd(c1, c2):
    """
    Add one polynomial to another.

    Returns the sum of two polynomials `c1` + `c2`.  The arguments are
    sequences of coefficients from lowest order term to highest, i.e.,
    [1,2,3] represents the polynomial ``1 + 2*x + 3*x**2"``.

    Parameters
    ----------
    c1, c2 : array_like
        1-d arrays of polynomial coefficients ordered from low to high.

    Returns
    -------
    out : ndarray
        The coefficient array representing their sum.

    See Also
    --------
    polysub, polymul, polydiv, polypow

    Examples
    --------
    >>> from numpy import polynomial as P
    >>> c1 = (1,2,3)
    >>> c2 = (3,2,1)
    >>> sum = P.polyadd(c1,c2); sum
    array([ 4.,  4.,  4.])
    >>> P.polyval(2, sum) # 4 + 4(2) + 4(2**2)
    28.0

    """
    # c1, c2 are trimmed copies
    [c1, c2] = pu.as_series([c1, c2])
    if len(c1) > len(c2) :
        c1[:c2.size] += c2
        ret = c1
    else :
        c2[:c1.size] += c1
        ret = c2
    return pu.trimseq(ret)


def polysub(c1, c2):
    """
    Subtract one polynomial from another.

    Returns the difference of two polynomials `c1` - `c2`.  The arguments
    are sequences of coefficients from lowest order term to highest, i.e.,
    [1,2,3] represents the polynomial ``1 + 2*x + 3*x**2``.

    Parameters
    ----------
    c1, c2 : array_like
        1-d arrays of polynomial coefficients ordered from low to
        high.

    Returns
    -------
    out : ndarray
        Of coefficients representing their difference.

    See Also
    --------
    polyadd, polymul, polydiv, polypow

    Examples
    --------
    >>> from numpy import polynomial as P
    >>> c1 = (1,2,3)
    >>> c2 = (3,2,1)
    >>> P.polysub(c1,c2)
    array([-2.,  0.,  2.])
    >>> P.polysub(c2,c1) # -P.polysub(c1,c2)
    array([ 2.,  0., -2.])

    """
    # c1, c2 are trimmed copies
    [c1, c2] = pu.as_series([c1, c2])
    if len(c1) > len(c2) :
        c1[:c2.size] -= c2
        ret = c1
    else :
        c2 = -c2
        c2[:c1.size] += c1
        ret = c2
    return pu.trimseq(ret)


def polymulx(cs):
    """Multiply a polynomial by x.

    Multiply the polynomial `cs` by x, where x is the independent
    variable.


    Parameters
    ----------
    cs : array_like
        1-d array of polynomial coefficients ordered from low to
        high.

    Returns
    -------
    out : ndarray
        Array representing the result of the multiplication.

    Notes
    -----
    .. versionadded:: 1.5.0

    """
    # cs is a trimmed copy
    [cs] = pu.as_series([cs])
    # The zero series needs special treatment
    if len(cs) == 1 and cs[0] == 0:
        return cs

    prd = np.empty(len(cs) + 1, dtype=cs.dtype)
    prd[0] = cs[0]*0
    prd[1:] = cs
    return prd


def polymul(c1, c2):
    """
    Multiply one polynomial by another.

    Returns the product of two polynomials `c1` * `c2`.  The arguments are
    sequences of coefficients, from lowest order term to highest, e.g.,
    [1,2,3] represents the polynomial ``1 + 2*x + 3*x**2.``

    Parameters
    ----------
    c1, c2 : array_like
        1-d arrays of coefficients representing a polynomial, relative to the
        "standard" basis, and ordered from lowest order term to highest.

    Returns
    -------
    out : ndarray
        Of the coefficients of their product.

    See Also
    --------
    polyadd, polysub, polydiv, polypow

    Examples
    --------
    >>> import numpy.polynomial as P
    >>> c1 = (1,2,3)
    >>> c2 = (3,2,1)
    >>> P.polymul(c1,c2)
    array([  3.,   8.,  14.,   8.,   3.])

    """
    # c1, c2 are trimmed copies
    [c1, c2] = pu.as_series([c1, c2])
    ret = np.convolve(c1, c2)
    return pu.trimseq(ret)


def polydiv(c1, c2):
    """
    Divide one polynomial by another.

    Returns the quotient-with-remainder of two polynomials `c1` / `c2`.
    The arguments are sequences of coefficients, from lowest order term
    to highest, e.g., [1,2,3] represents ``1 + 2*x + 3*x**2``.

    Parameters
    ----------
    c1, c2 : array_like
        1-d arrays of polynomial coefficients ordered from low to high.

    Returns
    -------
    [quo, rem] : ndarrays
        Of coefficient series representing the quotient and remainder.

    See Also
    --------
    polyadd, polysub, polymul, polypow

    Examples
    --------
    >>> import numpy.polynomial as P
    >>> c1 = (1,2,3)
    >>> c2 = (3,2,1)
    >>> P.polydiv(c1,c2)
    (array([ 3.]), array([-8., -4.]))
    >>> P.polydiv(c2,c1)
    (array([ 0.33333333]), array([ 2.66666667,  1.33333333]))

    """
    # c1, c2 are trimmed copies
    [c1, c2] = pu.as_series([c1, c2])
    if c2[-1] == 0 :
        raise ZeroDivisionError()

    len1 = len(c1)
    len2 = len(c2)
    if len2 == 1 :
        return c1/c2[-1], c1[:1]*0
    elif len1 < len2 :
        return c1[:1]*0, c1
    else :
        dlen = len1 - len2
        scl = c2[-1]
        c2  = c2[:-1]/scl
        i = dlen
        j = len1 - 1
        while i >= 0 :
            c1[i:j] -= c2*c1[j]
            i -= 1
            j -= 1
        return c1[j+1:]/scl, pu.trimseq(c1[:j+1])


def polypow(cs, pow, maxpower=None) :
    """Raise a polynomial to a power.

    Returns the polynomial `cs` raised to the power `pow`. The argument
    `cs` is a sequence of coefficients ordered from low to high. i.e.,
    [1,2,3] is the series  ``1 + 2*x + 3*x**2.``

    Parameters
    ----------
    cs : array_like
        1d array of array of series coefficients ordered from low to
        high degree.
    pow : integer
        Power to which the series will be raised
    maxpower : integer, optional
        Maximum power allowed. This is mainly to limit growth of the series
        to umanageable size. Default is 16

    Returns
    -------
    coef : ndarray
        Power series of power.

    See Also
    --------
    polyadd, polysub, polymul, polydiv

    Examples
    --------

    """
    # cs is a trimmed copy
    [cs] = pu.as_series([cs])
    power = int(pow)
    if power != pow or power < 0 :
        raise ValueError("Power must be a non-negative integer.")
    elif maxpower is not None and power > maxpower :
        raise ValueError("Power is too large")
    elif power == 0 :
        return np.array([1], dtype=cs.dtype)
    elif power == 1 :
        return cs
    else :
        # This can be made more efficient by using powers of two
        # in the usual way.
        prd = cs
        for i in range(2, power + 1) :
            prd = np.convolve(prd, cs)
        return prd


def polyder(c, m=1, scl=1, axis=0):
    """
    Differentiate a polynomial.

    Returns the polynomial coefficients `c` differentiated `m` times along
    `axis`.  At each iteration the result is multiplied by `scl` (the
    scaling factor is for use in a linear change of variable).  The
    argument `c` is an array of coefficients from low to high degree along
    each axis, e.g., [1,2,3] represents the polynomial ``1 + 2*x + 3*x**2``
    while [[1,2],[1,2]] represents ``1 + 1*x + 2*y + 2*x*y`` if axis=0 is
    ``x`` and axis=1 is ``y``.

    Parameters
    ----------
    c: array_like
        Array of polynomial coefficients. If c is multidimensional the
        different axis correspond to different variables with the degree
        in each axis given by the corresponding index.
    m : int, optional
        Number of derivatives taken, must be non-negative. (Default: 1)
    scl : scalar, optional
        Each differentiation is multiplied by `scl`.  The end result is
        multiplication by ``scl**m``.  This is for use in a linear change
        of variable. (Default: 1)
    axis : int, optional
        Axis over which the derivative is taken. (Default: 0).

    Returns
    -------
    der : ndarray
        Polynomial coefficients of the derivative.

    See Also
    --------
    polyint

    Examples
    --------
    >>> from numpy import polynomial as P
    >>> c = (1,2,3,4) # 1 + 2x + 3x**2 + 4x**3
    >>> P.polyder(c) # (d/dx)(c) = 2 + 6x + 12x**2
    array([  2.,   6.,  12.])
    >>> P.polyder(c,3) # (d**3/dx**3)(c) = 24
    array([ 24.])
    >>> P.polyder(c,scl=-1) # (d/d(-x))(c) = -2 - 6x - 12x**2
    array([ -2.,  -6., -12.])
    >>> P.polyder(c,2,-1) # (d**2/d(-x)**2)(c) = 6 + 24x
    array([  6.,  24.])

    """
    c = np.array(c, ndmin=1, copy=1)
    if c.dtype.char in '?bBhHiIlLqQpP':
        c = c.astype(np.double)
    cnt, iaxis = [int(t) for t in [m, axis]]

    if cnt != m:
        raise ValueError("The order of derivation must be integer")
    if cnt < 0:
        raise ValueError("The order of derivation must be non-negative")
    if iaxis != axis:
        raise ValueError("The axis must be integer")
    if not -c.ndim <= iaxis < c.ndim:
        raise ValueError("The axis is out of range")
    if iaxis < 0:
        iaxis += c.ndim

    if cnt == 0:
        return c

    c = np.rollaxis(c, iaxis)
    n = len(c)
    if cnt >= n:
        c = c[:1]*0
    else :
        for i in range(cnt):
            n = n - 1
            c *= scl
            der = np.empty((n,) + c.shape[1:], dtype=c.dtype)
            for j in range(n, 0, -1):
                der[j - 1] = j*c[j]
            c = der
    c = np.rollaxis(c, 0, iaxis + 1)
    return c


def polyint(c, m=1, k=[], lbnd=0, scl=1, axis=0):
    """
    Integrate a polynomial.

    Returns the polynomial coefficients `c` integrated `m` times from
    `lbnd` along `axis`.  At each iteration the resulting series is
    **multiplied** by `scl` and an integration constant, `k`, is added.
    The scaling factor is for use in a linear change of variable.  ("Buyer
    beware": note that, depending on what one is doing, one may want `scl`
    to be the reciprocal of what one might expect; for more information,
    see the Notes section below.) The argument `c` is an array of
    coefficients, from low to high degree along each axis, e.g., [1,2,3]
    represents the polynomial ``1 + 2*x + 3*x**2`` while [[1,2],[1,2]]
    represents ``1 + 1*x + 2*y + 2*x*y`` if axis=0 is ``x`` and axis=1 is
    ``y``.

    Parameters
    ----------
    c : array_like
        1-d array of polynomial coefficients, ordered from low to high.
    m : int, optional
        Order of integration, must be positive. (Default: 1)
    k : {[], list, scalar}, optional
        Integration constant(s).  The value of the first integral at zero
        is the first value in the list, the value of the second integral
        at zero is the second value, etc.  If ``k == []`` (the default),
        all constants are set to zero.  If ``m == 1``, a single scalar can
        be given instead of a list.
    lbnd : scalar, optional
        The lower bound of the integral. (Default: 0)
    scl : scalar, optional
        Following each integration the result is *multiplied* by `scl`
        before the integration constant is added. (Default: 1)
    axis : int, optional
        Axis over which the integral is taken. (Default: 0).

    Returns
    -------
    S : ndarray
        Coefficient array of the integral.

    Raises
    ------
    ValueError
        If ``m < 1``, ``len(k) > m``.

    See Also
    --------
    polyder

    Notes
    -----
    Note that the result of each integration is *multiplied* by `scl`.
    Why is this important to note?  Say one is making a linear change of
    variable :math:`u = ax + b` in an integral relative to `x`.  Then
    :math:`dx = du/a`, so one will need to set `scl` equal to :math:`1/a`
    - perhaps not what one would have first thought.

    Examples
    --------
    >>> from numpy import polynomial as P
    >>> c = (1,2,3)
    >>> P.polyint(c) # should return array([0, 1, 1, 1])
    array([ 0.,  1.,  1.,  1.])
    >>> P.polyint(c,3) # should return array([0, 0, 0, 1/6, 1/12, 1/20])
    array([ 0.        ,  0.        ,  0.        ,  0.16666667,  0.08333333,
            0.05      ])
    >>> P.polyint(c,k=3) # should return array([3, 1, 1, 1])
    array([ 3.,  1.,  1.,  1.])
    >>> P.polyint(c,lbnd=-2) # should return array([6, 1, 1, 1])
    array([ 6.,  1.,  1.,  1.])
    >>> P.polyint(c,scl=-2) # should return array([0, -2, -2, -2])
    array([ 0., -2., -2., -2.])

    """
    c = np.array(c, ndmin=1, copy=1)
    if c.dtype.char in '?bBhHiIlLqQpP':
        c = c.astype(np.double)
    if not np.iterable(k):
        k = [k]
    cnt, iaxis = [int(t) for t in [m, axis]]

    if cnt != m:
        raise ValueError("The order of integration must be integer")
    if cnt < 0 :
        raise ValueError("The order of integration must be non-negative")
    if len(k) > cnt :
        raise ValueError("Too many integration constants")
    if iaxis != axis:
        raise ValueError("The axis must be integer")
    if not -c.ndim <= iaxis < c.ndim:
        raise ValueError("The axis is out of range")
    if iaxis < 0:
        iaxis += c.ndim


    if cnt == 0:
        return c

    k = list(k) + [0]*(cnt - len(k))
    c = np.rollaxis(c, iaxis)
    for i in range(cnt):
        n = len(c)
        c *= scl
        if n == 1 and np.all(c[0] == 0):
            c[0] += k[i]
        else:
            tmp = np.empty((n + 1,) + c.shape[1:], dtype=c.dtype)
            tmp[0] = c[0]*0
            tmp[1] = c[0]
            for j in range(1, n):
                tmp[j + 1] = c[j]/(j + 1)
            tmp[0] += k[i] - polyval(lbnd, tmp)
            c = tmp
    c = np.rollaxis(c, 0, iaxis + 1)
    return c


def polyval(x, c, tensor=True):
    """
    Evaluate a polynomial.

    If `c` is of length ``n + 1``, this function returns the value:

    ``p(x) = c[0] + c[1]*x + ... + c[n]*x**(n)``

    If `x` is a sequence or array and `c` is 1 dimensional, then ``p(x)``
    will have the same shape as `x`.  If `x` is a algebra_like object that
    supports multiplication and addition with itself and the values in `c`,
    then an object of the same type is returned.

    In the case where c is multidimensional, the shape of the result
    depends on the value of `tensor`. If tensor is true the shape of the
    return will be ``c.shape[1:] + x.shape``, where the shape of a scalar
    is the empty tuple. If tensor is false the shape is ``c.shape[1:]`` if
    `x` is broadcast compatible with that.

    If there are trailing zeros in the coefficients they still take part in
    the evaluation, so they should be avoided if efficiency is a concern.

    Parameters
    ----------
    x : array_like, algebra_like
        If x is a list or tuple, it is converted to an ndarray. Otherwise
        it is left unchanged and if it isn't an ndarray it is treated as a
        scalar. In either case, `x` or any element of an ndarray must
        support addition and multiplication with itself and the elements of
        `c`.
    c : array_like
        Array of coefficients ordered so that the coefficients for terms of
        degree n are contained in ``c[n]``. If `c` is multidimesional the
        remaining indices enumerate multiple polynomials. In the two
        dimensional case the coefficients may be thought of as stored in
        the columns of `c`.
    tensor : boolean, optional
        If true, the coefficient array shape is extended with ones on the
        right, one for each dimension of `x`. Scalars are treated as having
        dimension 0 for this action. The effect is that every column of
        coefficients in `c` is evaluated for every value in `x`. If False,
        the `x` are broadcast over the columns of `c` in the usual way.
        This gives some flexibility in evaluations in the multidimensional
        case. The default value it ``True``.

    Returns
    -------
    values : ndarray, algebra_like
        The shape of the return value is described above.

    See Also
    --------
    polyval2d, polygrid2d, polyval3d, polygrid3d

    Notes
    -----
    The evaluation uses Horner's method.

    Examples
    --------
    >>> from numpy.polynomial.polynomial import polyval
    >>> polyval(1, [1,2,3])
    6.0
    >>> a = np.arange(4).reshape(2,2)
    >>> a
    array([[[  0,   1],
            [  2,   3]],
    >>> polyval(a, [1,2,3])
    array([[  1.,   6.],
           [ 17.,  34.]])
    >>> c = np.arange(4).reshape(2,2)
    >>> c
    array([[[  0,   1],
            [  2,   3]],
    >>> polyval([1,2], c, tensor=True)
    array([[ 2.,  4.],
           [ 4.,  7.]])
    >>> polyval([1,2], c, tensor=False)
    array([ 2.,  7.])

    """
    c = np.array(c, ndmin=1, copy=0)
    if c.dtype.char in '?bBhHiIlLqQpP':
        c = c.astype(np.double)
    if isinstance(x, (tuple, list)):
        x = np.asarray(x)
    if isinstance(x, np.ndarray) and tensor:
        c = c.reshape(c.shape + (1,)*x.ndim)

    c0 = c[-1] + x*0
    for i in range(2, len(c) + 1) :
        c0 = c[-i] + c0*x
    return c0


def polyval2d(x, y, c):
    """
    Evaluate 2D polynomials at points (x,y).

    This function returns the values:

    ``p(x,y) = \sum_{i,j} c[i,j] * x^i * y^j``

    Parameters
    ----------
    x,y : array_like, algebra_like
        The two dimensional polynomial is evaluated at the points
        ``(x,y)``, where `x` and `y` must have the same shape. If `x` or
        `y` is a list or tuple, it is first converted to an ndarray,
        otherwise it is left unchanged and if it isn't an ndarray it is
        treated as a scalar. See `polyval` for explanation of algebra_like.
    c : array_like
        Array of coefficients ordered so that the coefficients for terms of
        degree i,j are contained in ``c[i,j]``. If `c` has dimension
        greater than 2 the remaining indices enumerate multiple sets of
        coefficients.

    Returns
    -------
    values : ndarray, algebra_like
        The values of the two dimensional polynomial at points formed with
        pairs of corresponding values from `x` and `y`.

    See Also
    --------
    polyval, polygrid2d, polyval3d, polygrid3d

    """
    return polyval(y, polyval(x, c), False)


def polygrid2d(x, y, c):
    """
    Evaluate 2D polynomials on the Cartesion product of x,y.

    This function returns the values:

    ``p(a,b) = \sum_{i,j} c[i,j] * a^i * b^j``

    where the points ``(a,b)`` consist of all pairs of points formed by
    taking ``a`` from `x` and ``b`` from `y`. The resulting points form a
    grid with `x` in the first dimension and `y` in the second.

    Parameters
    ----------
    x,y : array_like, algebra_like
        The two dimensional polynomial is evaluated at the points in the
        Cartesian product of `x` and `y`.  If `x` or `y` is a list or
        tuple, it is first converted to an ndarray, otherwise it is left
        unchanged and if it isn't an ndarray it is treated as a scalar. See
        `polyval` for explanation of algebra_like.
    c : array_like
        Array of coefficients ordered so that the coefficients for terms of
        degree i,j are contained in ``c[i,j]``. If `c` has dimension
        greater than 2 the remaining indices enumerate multiple sets of
        coefficients.

    Returns
    -------
    values : ndarray, algebra_like
        The values of the two dimensional polynomial at points in the Cartesion
        product of `x` and `y`.

    See Also
    --------
    polyval, polyval2d, polyval3d, polygrid3d

    """
    return polyval(y, polyval(x, c))


def polyval3d(x, y, z, c):
    """
    Evaluate 3D polynomials at points (x,y,z).

    This function returns the values:

    ``p(x,y,z) = \sum_{i,j,k} c[i,j,k] * x^i * y^j * z^k``

    Parameters
    ----------
    x,y,z : array_like, algebra_like
        The three dimensional polynomial is evaluated at the points
        ``(x,y,z)``, where `x`, `y`, and `z` must have the same shape.  If
        any of `x`, `y`, or `z` is a list or tuple, it is first converted
        to an ndarray, otherwise it is left unchanged and if it isn't an
        ndarray it is  treated as a scalar. See `polyval` for an
        explanation of algebra_like.
    c : array_like
        Array of coefficients ordered so that the coefficients for terms of
        degree i, j are contained in ``c[i,j,k]``. If `c` has dimension
        greater than 3 the remaining indices enumerate multiple sets of
        coefficients.

    Returns
    -------
    values : ndarray, algebra_like
        The values of the multidimension polynomial on points formed with
        triples of corresponding values from `x`, `y`, and `z`.

    See Also
    --------
    polyval, polyval2d, polygrid2d, polygrid3d

    """
    return polyval(z, polyval2d(x, y, c), False)


def polygrid3d(x, y, z, c):
    """
    Evaluate 3D polynomials on the Cartesion product of x,y,z.

    This function returns the values:

    ``p(a,b,c) = \sum_{i,j,k} c[i,j,k] * a^i * b^j * c^k``

    where the points ``(a,b,c)`` consist of all triples formed by taking
    ``a`` from `x`, ``b`` from `y`, and ``c`` from `z`. The resulting
    points form a grid with `x` in the first dimension, `y` in the second,
    and `z` in the third.

    Parameters
    ----------
    x,y,z : array_like, algebra_like
        The three dimensional polynomial is evaluated at the points
        ``(x,y,z)``, where `x` and `y` must have the same shape. If `x` or
        `y` is a list or tuple, it is first converted to an ndarray,
        otherwise it is left unchanged and treated as a scalar. See
        `polyval` for explanation of algebra_like.
    c : array_like
        Array of coefficients ordered so that the coefficients for terms of
        degree i,j are contained in ``c[i,j,k]``. If `c` has dimension
        greater than 3 the remaining indices enumerate multiple sets of
        coefficients.

    Returns
    -------
    values : ndarray, algebra_like
        The values of the multidimensional polynomial on the cartesion
        product of `x`, `y`, and `z`.

    See Also
    --------
    polyval, polyval2d, polygrid2d, polyval3d

    """
    return polyval(z, polygrid2d(x, y, c))


def polyvander(x, deg) :
    """Vandermonde matrix of given degree.

    Returns the Vandermonde matrix of degree `deg` and sample points `x`.
    This isn't a true Vandermonde matrix because `x` can be an arbitrary
    ndarray. If ``V`` is the returned matrix and `x` is a 2d array, then
    the elements of ``V`` are ``V[i,j,k] = x[i,j]**k``

    Parameters
    ----------
    x : array_like
        Array of points. The values are converted to double or complex
        doubles. If x is scalar it is converted to a 1D array.
    deg : integer
        Degree of the resulting matrix.

    Returns
    -------
    vander : Vandermonde matrix.
        The shape of the returned matrix is ``x.shape + (deg+1,)``. The last
        index is the degree.

    See Also
    --------
    polyvander2d, polyvander3d

    """
    ideg = int(deg)
    if ideg != deg:
        raise ValueError("deg must be integer")
    if ideg < 0:
        raise ValueError("deg must be non-negative")

    x = np.array(x, copy=0, ndmin=1) + 0.0
    v = np.empty((ideg + 1,) + x.shape, dtype=x.dtype)
    v[0] = x*0 + 1
    if ideg > 0 :
        v[1] = x
        for i in range(2, ideg + 1) :
            v[i] = v[i-1]*x
    return np.rollaxis(v, 0, v.ndim)


def polyvander2d(x, y, deg) :
    """Pseudo Vandermonde matrix of given degree.

    Returns the pseudo Vandermonde matrix for 2D polynomials in `x` and
    `y`. The sample point coordinates must all have the same shape after
    conversion to arrays and the dtype will be converted to either float64
    or complex128 depending on whether any of `x` or 'y' are complex.  The
    maximum degrees of the 2D polynomials in each variable are specified in
    the list `deg` in the form ``[xdeg, ydeg]``. The return array has the
    shape ``x.shape + (order,)`` if `x`, and `y` are arrays or ``(1, order)
    if they are scalars. Here order is the number of elements in a
    flattened coefficient array of original shape ``(xdeg + 1, ydeg + 1)``.
    The flattening is done so that the resulting pseudo Vandermonde array
    can be easily used in least squares fits.

    Parameters
    ----------
    x,y : array_like
        Arrays of point coordinates, each of the same shape.
    deg : list
        List of maximum degrees of the form [x_deg, y_deg].

    Returns
    -------
    vander2d : ndarray
        The shape of the returned matrix is described above.

    See Also
    --------
    polyvander, polyvander3d. polyval2d, polyval3d

    """
    ideg = [int(d) for d in deg]
    is_valid = [id == d and id >= 0 for id, d in zip(ideg, deg)]
    if is_valid != [1, 1]:
        raise ValueError("degrees must be non-negative integers")
    degx, degy = deg
    x, y = np.array((x, y), copy=0) + 0.0

    vx = polyvander(x, degx)
    vy = polyvander(y, degy)
    v = np.einsum("...i,...j->...ij", vx, vy)
    return v.reshape(v.shape[:-2] + (-1,))


def polyvander3d(x, y, z, deg) :
    """Psuedo Vandermonde matrix of given degree.

    Returns the pseudo Vandermonde matrix for 3D polynomials in `x`, `y`,
    or `z`. The sample point coordinates must all have the same shape after
    conversion to arrays and the dtype will be converted to either float64
    or complex128 depending on whether any of `x`, `y`, or 'z' are complex.
    The maximum degrees of the 3D polynomials in each variable are
    specified in the list `deg` in the form ``[xdeg, ydeg, zdeg]``. The
    return array has the shape ``x.shape + (order,)`` if `x`, `y`, and `z`
    are arrays or ``(1, order) if they are scalars. Here order is the
    number of elements in a flattened coefficient array of original shape
    ``(xdeg + 1, ydeg + 1, zdeg + 1)``.  The flattening is done so that the
    resulting pseudo Vandermonde array can be easily used in least squares
    fits.

    Parameters
    ----------
    x,y,z : array_like
        Arrays of point coordinates, each of the same shape.
    deg : list
        List of maximum degrees of the form [x_deg, y_deg, z_deg].

    Returns
    -------
    vander3d : ndarray
        The shape of the returned matrix is described above.

    See Also
    --------
    polyvander, polyvander3d. polyval2d, polyval3d

    """
    ideg = [int(d) for d in deg]
    is_valid = [id == d and id >= 0 for id, d in zip(ideg, deg)]
    if is_valid != [1, 1, 1]:
        raise ValueError("degrees must be non-negative integers")
    degx, degy, degz = deg
    x, y, z = np.array((x, y, z), copy=0) + 0.0

    vx = polyvander(x, deg_x)
    vy = polyvander(y, deg_y)
    vz = polyvander(z, deg_z)
    v = np.einsum("...i,...j,...k->...ijk", vx, vy, vz)
    return v.reshape(v.shape[:-3] + (-1,))


def polyfit(x, y, deg, rcond=None, full=False, w=None):
    """
    Least-squares fit of a polynomial to data.

    Fit a polynomial ``c0 + c1*x + c2*x**2 + ... + c[deg]*x**deg`` to
    points (`x`, `y`).  Returns a 1-d (if `y` is 1-d) or 2-d (if `y` is 2-d)
    array of coefficients representing, from lowest order term to highest,
    the polynomial(s) which minimize the total square error.

    Parameters
    ----------
    x : array_like, shape (`M`,)
        x-coordinates of the `M` sample (data) points ``(x[i], y[i])``.
    y : array_like, shape (`M`,) or (`M`, `K`)
        y-coordinates of the sample points.  Several sets of sample points
        sharing the same x-coordinates can be (independently) fit with one
        call to `polyfit` by passing in for `y` a 2-d array that contains
        one data set per column.
    deg : int
        Degree of the polynomial(s) to be fit.
    rcond : float, optional
        Relative condition number of the fit.  Singular values smaller
        than `rcond`, relative to the largest singular value, will be
        ignored.  The default value is ``len(x)*eps``, where `eps` is the
        relative precision of the platform's float type, about 2e-16 in
        most cases.
    full : bool, optional
        Switch determining the nature of the return value.  When ``False``
        (the default) just the coefficients are returned; when ``True``,
        diagnostic information from the singular value decomposition (used
        to solve the fit's matrix equation) is also returned.
    w : array_like, shape (`M`,), optional
        Weights. If not None, the contribution of each point
        ``(x[i],y[i])`` to the fit is weighted by `w[i]`. Ideally the
        weights are chosen so that the errors of the products ``w[i]*y[i]``
        all have the same variance.  The default value is None.
        .. versionadded:: 1.5.0

    Returns
    -------
    coef : ndarray, shape (`deg` + 1,) or (`deg` + 1, `K`)
        Polynomial coefficients ordered from low to high.  If `y` was 2-d,
        the coefficients in column `k` of `coef` represent the polynomial
        fit to the data in `y`'s `k`-th column.

    [residuals, rank, singular_values, rcond] : present when `full` == True
        Sum of the squared residuals (SSR) of the least-squares fit; the
        effective rank of the scaled Vandermonde matrix; its singular
        values; and the specified value of `rcond`.  For more information,
        see `linalg.lstsq`.

    Raises
    ------
    RankWarning
        Raised if the matrix in the least-squares fit is rank deficient.
        The warning is only raised if `full` == False.  The warnings can
        be turned off by:

        >>> import warnings
        >>> warnings.simplefilter('ignore', RankWarning)

    See Also
    --------
    polyval : Evaluates a polynomial.
    polyvander : Vandermonde matrix for powers.
    chebfit : least squares fit using Chebyshev series.
    linalg.lstsq : Computes a least-squares fit from the matrix.
    scipy.interpolate.UnivariateSpline : Computes spline fits.

    Notes
    -----
    The solutions are the coefficients ``c[i]`` of the polynomial ``P(x)``
    that minimizes the total squared error:

    .. math :: E = \\sum_j (y_j - P(x_j))^2

    This problem is solved by setting up the (typically) over-determined
    matrix equation:

    .. math :: V(x)*c = y

    where `V` is the Vandermonde matrix of `x`, the elements of `c` are the
    coefficients to be solved for, and the elements of `y` are the observed
    values.  This equation is then solved using the singular value
    decomposition of `V`.

    If some of the singular values of `V` are so small that they are
    neglected (and `full` == ``False``), a `RankWarning` will be raised.
    This means that the coefficient values may be poorly determined.
    Fitting to a lower order polynomial will usually get rid of the warning
    (but may not be what you want, of course; if you have independent
    reason(s) for choosing the degree which isn't working, you may have to:
    a) reconsider those reasons, and/or b) reconsider the quality of your
    data).  The `rcond` parameter can also be set to a value smaller than
    its default, but the resulting fit may be spurious and have large
    contributions from roundoff error.

    Polynomial fits using double precision tend to "fail" at about
    (polynomial) degree 20. Fits using Chebyshev series are generally
    better conditioned, but much can still depend on the distribution of
    the sample points and the smoothness of the data.  If the quality of
    the fit is inadequate, splines may be a good alternative.

    Examples
    --------
    >>> from numpy import polynomial as P
    >>> x = np.linspace(-1,1,51) # x "data": [-1, -0.96, ..., 0.96, 1]
    >>> y = x**3 - x + np.random.randn(len(x)) # x^3 - x + N(0,1) "noise"
    >>> c, stats = P.polyfit(x,y,3,full=True)
    >>> c # c[0], c[2] should be approx. 0, c[1] approx. -1, c[3] approx. 1
    array([ 0.01909725, -1.30598256, -0.00577963,  1.02644286])
    >>> stats # note the large SSR, explaining the rather poor results
    [array([ 38.06116253]), 4, array([ 1.38446749,  1.32119158,  0.50443316,
    0.28853036]), 1.1324274851176597e-014]

    Same thing without the added noise

    >>> y = x**3 - x
    >>> c, stats = P.polyfit(x,y,3,full=True)
    >>> c # c[0], c[2] should be "very close to 0", c[1] ~= -1, c[3] ~= 1
    array([ -1.73362882e-17,  -1.00000000e+00,  -2.67471909e-16,
             1.00000000e+00])
    >>> stats # note the minuscule SSR
    [array([  7.46346754e-31]), 4, array([ 1.38446749,  1.32119158,
    0.50443316,  0.28853036]), 1.1324274851176597e-014]

    """
    order = int(deg) + 1
    x = np.asarray(x) + 0.0
    y = np.asarray(y) + 0.0

    # check arguments.
    if deg < 0 :
        raise ValueError("expected deg >= 0")
    if x.ndim != 1:
        raise TypeError("expected 1D vector for x")
    if x.size == 0:
        raise TypeError("expected non-empty vector for x")
    if y.ndim < 1 or y.ndim > 2 :
        raise TypeError("expected 1D or 2D array for y")
    if len(x) != len(y):
        raise TypeError("expected x and y to have same length")

    # set up the least squares matrices
    lhs = polyvander(x, deg)
    rhs = y
    if w is not None:
        w = np.asarray(w) + 0.0
        if w.ndim != 1:
            raise TypeError("expected 1D vector for w")
        if len(x) != len(w):
            raise TypeError("expected x and w to have same length")
        # apply weights
        if rhs.ndim == 2:
            lhs *= w[:, np.newaxis]
            rhs *= w[:, np.newaxis]
        else:
            lhs *= w[:, np.newaxis]
            rhs *= w

    # set rcond
    if rcond is None :
        rcond = len(x)*np.finfo(x.dtype).eps

    # scale the design matrix and solve the least squares equation
    scl = np.sqrt((lhs*lhs).sum(0))
    c, resids, rank, s = la.lstsq(lhs/scl, rhs, rcond)
    c = (c.T/scl).T

    # warn on rank reduction
    if rank != order and not full:
        msg = "The fit may be poorly conditioned"
        warnings.warn(msg, pu.RankWarning)

    if full :
        return c, [resids, rank, s, rcond]
    else :
        return c


def polyroots(cs):
    """
    Compute the roots of a polynomial.

    Return the roots (a.k.a. "zeros") of the "polynomial" `cs`, the
    polynomial's coefficients from lowest order term to highest
    (e.g., [1,2,3] represents the polynomial ``1 + 2*x + 3*x**2``).

    Parameters
    ----------
    cs : array_like of shape (M,)
        1-d array of polynomial coefficients ordered from low to high.

    Returns
    -------
    out : ndarray
        Array of the roots of the polynomial.  If all the roots are real,
        then so is the dtype of ``out``; otherwise, ``out``'s dtype is
        complex.

    See Also
    --------
    chebroots

    Examples
    --------
    >>> import numpy.polynomial as P
    >>> P.polyroots(P.polyfromroots((-1,0,1)))
    array([-1.,  0.,  1.])
    >>> P.polyroots(P.polyfromroots((-1,0,1))).dtype
    dtype('float64')
    >>> j = complex(0,1)
    >>> P.polyroots(P.polyfromroots((-j,0,j)))
    array([  0.00000000e+00+0.j,   0.00000000e+00+1.j,   2.77555756e-17-1.j])

    """
    # cs is a trimmed copy
    [cs] = pu.as_series([cs])
    if len(cs) <= 1 :
        return np.array([], dtype=cs.dtype)
    if len(cs) == 2 :
        return np.array([-cs[0]/cs[1]])

    n = len(cs) - 1
    cmat = np.zeros((n,n), dtype=cs.dtype)
    cmat.flat[n::n+1] = 1
    cmat[:,-1] -= cs[:-1]/cs[-1]
    roots = la.eigvals(cmat)
    roots.sort()
    return roots


#
# polynomial class
#

exec polytemplate.substitute(name='Polynomial', nick='poly', domain='[-1,1]')

