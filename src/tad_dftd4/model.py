import torch
import numpy as np
from pathlib import Path

from ._typing import Tensor, Any, TensorLike
from . import data


ref = np.load(Path(Path(__file__).parent, "params.npz"))

# fmt: off
refn = torch.tensor([
  0, 2, 1, 3, 4, 5, 7, 5, 4, 2, 1, 3, 4, 4, 5, 4, 3, 2, 1, 3, 4, 4,
  4, 4, 4, 3, 3, 4, 4, 2, 2, 3, 5, 4, 3, 2, 1, 3, 4, 3, 4, 4, 4, 3,
  3, 4, 3, 2, 2, 4, 5, 4, 3, 2, 1, 3, 4, 3, 1, 2, 2, 2, 2, 2, 2, 2,
  2, 2, 2, 2, 2, 2, 4, 4, 3, 3, 3, 5, 3, 2, 2, 4, 5, 4, 3, 2, 1,
])
# fmt: on

THOPI = 3.0 / 3.141592653589793238462643383279502884197


def load_from_npz(npzfile: Any, name: str, dtype: torch.dtype) -> Tensor:
    """
    Get torch tensor from npz file.

    Parameters
    ----------
    npzfile : Any
        Loaded npz file.
    name : str
        Name of the tensor in the npz file.
    dtype : torch.dtype
        Data type of the tensor.

    Returns
    -------
    Tensor
        Tensor from the npz file.
    """
    name = name.replace("-", "").replace("+", "").lower()
    return torch.from_numpy(npzfile[name]).type(dtype)


def trapzd(polarizability_a: Tensor, polarizability_b: Tensor) -> Tensor:
    """
    Numerical Casimir--Polder integration.

    Parameters
    ----------
    polarizability : Tensor
        Polarizabilities.

    Returns
    -------
    Tensor
        C6 coefficients.
    """
    weights = torch.tensor(
        [
            0.0499990000000000,
            0.0999990000000000,
            0.1500000000000000,
            0.2000000000000000,
            0.2000000000000000,
            0.2000000000000000,
            0.2000000000000000,
            0.2000000000000000,
            0.2000000000000000,
            0.2000000000000000,
            0.2000000000000000,
            0.3000000000000000,
            0.4000000000000000,
            0.4000000000000000,
            0.4000000000000000,
            0.4000000000000000,
            0.7000000000000000,
            1.0000000000000000,
            1.5000000000000000,
            2.0000000000000000,
            3.5000000000000000,
            5.0000000000000000,
            2.5000000000000000,
        ]
    )

    c6 = 0.0
    for w in range(23):
        c6 += weights[w] * polarizability_a[w] * polarizability_b[w]
    return 0.5 * c6

    # return torch.sum(weights * polarizability, dim=-1)


def weight_cn(wf: float, cn: Tensor, cnref: Tensor):
    dcn = cn - cnref
    return torch.exp(-wf * dcn * dcn)


def zeta(a, c, qref, qmod):
    if qmod <= 0.0:
        return torch.exp(a)

    return torch.exp(a * (1.0 - torch.exp(c * (1.0 - qref / qmod))))


ga_default = 3.0
gc_default = 2.0
wf_default = 6.0


class D4Model(TensorLike):
    """
    The D4 dispersion model.
    """

    ga: float = ga_default
    """Maximum charge scaling height for partial charge extrapolation."""

    gc: float = gc_default
    """Charge scaling steepness for partial charge extrapolation."""

    wf: float = wf_default
    """Weighting factor for coordination number interpolation."""

    def __init__(
        self,
        ga: float = ga_default,
        gc: float = gc_default,
        wf: float = wf_default,
        device: torch.device | None = None,
        dtype: torch.dtype | None = None,
    ) -> None:
        super().__init__(device, dtype)
        self.ga = ga
        self.gc = gc
        self.wf = wf

    def weight_references(
        self,
        numbers: Tensor,
        cn: Tensor | None = None,
        q: Tensor | None = None,
    ) -> Tensor:
        if cn is None:
            cn = torch.zeros_like(numbers, dtype=self.dtype)
        if q is None:
            q = torch.zeros_like(numbers, dtype=self.dtype)

        mref = torch.max(refn[numbers])
        gwvec = torch.zeros(mref, numbers.size(0), dtype=self.dtype)

        refc = load_from_npz(ref, "refc", torch.int8)
        refcn = load_from_npz(ref, "refcn", self.dtype)
        refq = load_from_npz(ref, "refq", self.dtype)
        mask = refc[numbers] > 0

        # zeff = data.zeff[numbers]
        # gam = data.gam[numbers] * self.gc
        # maxcn = torch.max(refcn[numbers], dim=-1)[0]
        dcn = cn.unsqueeze(-1) - refcn[numbers]
        tmp = torch.exp(-dcn * dcn)

        expw = torch.where(
            mask,
            torch.where(
                refc[numbers] == 3,
                torch.pow(tmp, self.wf)
                + torch.pow(tmp, 2 * self.wf)
                + torch.pow(tmp, 3 * self.wf),
                torch.where(
                    refc[numbers] == 1,
                    torch.pow(tmp, self.wf),
                    tmp,
                ),
            ),
            dcn.new_tensor(0.0),
        )

        norm = torch.sum(expw, dim=-1, keepdim=True)

        maxcn = torch.max(refcn[numbers], dim=-1, keepdim=True)[0]

        print(refcn[numbers] == maxcn)

        print("maxcn\n", torch.max(refcn[numbers], dim=-1))
        print("maxcn\n", torch.max(refcn[numbers]))

        gwk = expw / norm

        # prevent division by 0 and small values
        exceptional = (torch.isnan(norm)) | (norm > torch.finfo(self.dtype).max)
        print(exceptional)
        print("norm\n", norm)
        print("gwk\n", gwk)
        f = torch.where(
            exceptional,
            torch.where(
                refcn[numbers] == maxcn,
                gwk.new_tensor(1.0),
                gwk.new_tensor(0.0),
            ),
            gwk,
        )

        print(torch.where(exceptional, torch.ones_like(gwk), torch.zeros_like(gwk)))

        print("gwk\n", f)
        # zeta(self.ga, gi, refq[izp][iref] + zi, q[iat] + zi)
        def zeta2(scale, gam, qref, qmod):
            return torch.where(
                qmod <= 0.0,
                torch.exp(qmod.new_tensor(scale)),
                torch.exp(scale * (1.0 - torch.exp(gam * (1.0 - qref / qmod)))),
            )

        # unsqueeze for reference dimension
        zeff = data.zeff[numbers].unsqueeze(-1)
        gam = data.gam[numbers].unsqueeze(-1) * self.gc
        q = q.unsqueeze(-1)

        # FIXME: stop transposing
        z = zeta2(self.ga, gam, refq[numbers] + zeff, q + zeff)

        print("zeta\n", z)

        print((f * z).mT)

        gwks = torch.zeros_like(refq[numbers])

        for iat, izp in enumerate(numbers):
            izp = int(izp)
            zi = data.zeff[izp]
            gi = data.gam[izp] * self.gc

            norm = 0.0
            for iref in range(refn[izp]):
                dcn = cn[iat] - refcn[izp][iref]
                tmp = torch.exp(-dcn * dcn)
                for igw in range(refc[izp][iref]):
                    twf = (igw + 1) * self.wf
                    norm += torch.pow(tmp, twf)

            norm = 1.0 / norm

            for iref in range(refn[izp]):
                expw = 0.0

                for igw in range(refc[izp][iref]):
                    twf = (igw + 1) * self.wf
                    expw += weight_cn(twf, cn[iat], refcn[izp][iref])

                gwk = expw * norm

                if torch.isnan(torch.tensor(gwk)):
                    if refcn[izp][iref] == maxcn:
                        gwk = 1.0
                    else:
                        gwk = 0.0

                gwks[iat, iref] = gwk

                z = zeta(self.ga, gi, refq[izp][iref] + zi, q[iat] + zi)
                gwvec[iref, iat] = z * gwk

        print("\nrefs")
        print("gwks\n", gwks)
        print("gwvec\n", gwvec)

        return (f * z).mT
        return gwvec

    def _set_refalpha_eeq(self, numbers: Tensor):
        refsys = load_from_npz(ref, "refsys", torch.int8)
        refsq = load_from_npz(ref, "refsq", torch.float)
        refascale = load_from_npz(ref, "refascale", torch.float)
        refalpha = load_from_npz(ref, "refalpha", torch.float)
        refscount = load_from_npz(ref, "refscount", torch.float)
        secscale = load_from_npz(ref, "secscale", torch.float)
        secalpha = load_from_npz(ref, "secalpha", torch.float)

        mref = torch.max(refn[numbers])
        alpha = torch.zeros(numbers.size(-1), 23 * mref)

        for iat, izp in enumerate(numbers):
            izp = int(izp)

            for iref in range(refn[izp]):
                isys = refsys[izp][iref]
                iz = data.zeff[isys]
                ig = data.gam[isys] * self.gc

                for k in range(23):
                    aiw = (
                        secscale[isys]
                        * secalpha[isys][k]
                        * zeta(self.ga, ig, iz, refsq[izp][iref])
                    )
                    alpha[iat, 23 * iref + k] = max(
                        0.0,
                        float(
                            refascale[izp][iref]
                            * (
                                refalpha[izp][23 * iref + k]
                                - refscount[izp][iref] * aiw
                            )
                        ),
                    )

        return alpha

    def get_atomic_c6(self, numbers: Tensor, gwvec: Tensor) -> Tensor:
        """
        Calculate atomic dispersion coefficients.
        """

        alpha = self._set_refalpha_eeq(numbers)

        c6 = torch.zeros(numbers.size(-1), numbers.size(-1))

        for iat, izp in enumerate(numbers):
            izp = int(izp)
            for jat, jzp in enumerate(numbers):
                jzp = int(jzp)

                dc6 = 0.0
                for iref in range(refn[izp]):
                    for jref in range(refn[jzp]):
                        refc6 = THOPI * trapzd(
                            alpha[iat][23 * iref], alpha[jat][23 * jref]
                        )
                        dc6 += gwvec[iref, iat] * gwvec[jref, jat] * refc6

                c6[iat, jat] = dc6
                c6[jat, iat] = dc6

        return c6