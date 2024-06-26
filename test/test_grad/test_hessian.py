# This file is part of tad-dftd4.
#
# SPDX-Identifier: Apache-2.0
# Copyright (C) 2024 Grimme Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Testing dispersion Hessian (autodiff).

The reference values are calculated with the dftd4 standalone (Fortran) program,
version 3.6.0. However, some minor modifications are required to obtained a
compatible array ordering from Fortran. In Fortran, the shape of the Hessian is
`(3, mol%nat, 3, mol%nat)`, which we change to `(mol%nat, 3, mol%nat, 3)`.
Correspondingly, the calculation in `get_dispersion_hessian` must also be
adapted: We replace `hessian(:, :, ix, iat) = (gl - gr) / (2 * step)` by
`hessian(:, :, iat, ix) = (transpose(gl) - transpose(gr)) / (2 * step)`. The
Hessian can then simply be printed via `write(*, '(SP,es23.16e2,",")') hessian`
and the Python resorting is handled by the reshape function.
"""
from __future__ import annotations

import pytest
import torch
from tad_mctc.autograd import hessian
from tad_mctc.batch import pack
from tad_mctc.convert import reshape_fortran

from tad_dftd4 import dftd4
from tad_dftd4.typing import DD, Tensor

from ..conftest import DEVICE
from .samples_hessian import samples

sample_list = ["LiH", "SiH4", "PbH4-BiH3", "MB16_43_01"]

tol = 1e-7


def test_fail() -> None:
    sample = samples["LiH"]
    numbers = sample["numbers"]
    positions = sample["positions"]
    param = {"a1": numbers}

    # differentiable variable is not a tensor
    with pytest.raises(ValueError):
        hessian(dftd4, (numbers, positions, param), argnums=2)


def test_zeros() -> None:
    d = torch.randn(2, 3, requires_grad=True)
    zeros = torch.zeros([*d.shape, *d.shape])

    def dummy(x: Tensor) -> Tensor:
        return torch.zeros_like(x)

    hess = hessian(dummy, (d,), argnums=0)
    assert pytest.approx(zeros.cpu()) == hess.detach().cpu()


@pytest.mark.parametrize("dtype", [torch.double])
@pytest.mark.parametrize("name", sample_list)
def test_single(dtype: torch.dtype, name: str) -> None:
    dd: DD = {"device": DEVICE, "dtype": dtype}

    sample = samples[name]
    numbers = sample["numbers"].to(DEVICE)
    positions = sample["positions"].to(**dd)
    charge = torch.tensor(0.0, **dd)

    # TPSS0-ATM parameters
    param = {
        "s6": torch.tensor(1.00000000, **dd),
        "s8": torch.tensor(1.62438102, **dd),
        "s9": torch.tensor(1.00000000, **dd),
        "a1": torch.tensor(0.40329022, **dd),
        "a2": torch.tensor(4.80537871, **dd),
    }

    ref = reshape_fortran(
        sample["hessian"].to(**dd),
        torch.Size(2 * (numbers.shape[-1], 3)),
    )

    # variable to be differentiated
    positions.requires_grad_(True)

    hess = hessian(dftd4, (numbers, positions, charge, param), argnums=1)
    positions.detach_()

    assert pytest.approx(ref.cpu(), abs=tol, rel=tol) == hess.detach().cpu()


# TODO: Figure out batched Hessian computation
@pytest.mark.parametrize("dtype", [torch.double])
@pytest.mark.parametrize("name1", ["LiH"])
@pytest.mark.parametrize("name2", sample_list)
def skip_test_batch(dtype: torch.dtype, name1: str, name2: str) -> None:
    dd: DD = {"device": DEVICE, "dtype": dtype}

    sample1, sample2 = samples[name1], samples[name2]
    numbers = pack(
        [
            sample1["numbers"].to(DEVICE),
            sample2["numbers"].to(DEVICE),
        ]
    )
    positions = pack(
        [
            sample1["positions"].to(**dd),
            sample2["positions"].to(**dd),
        ]
    )
    charge = torch.tensor([0.0, 0.0], **dd)

    # TPSS0-ATM parameters
    param = {
        "s6": torch.tensor(1.00000000, **dd),
        "s8": torch.tensor(1.62438102, **dd),
        "s9": torch.tensor(1.00000000, **dd),
        "a1": torch.tensor(0.40329022, **dd),
        "a2": torch.tensor(4.80537871, **dd),
    }

    ref = pack(
        [
            reshape_fortran(
                sample1["hessian"].to(**dd),
                torch.Size(2 * (sample1["numbers"].shape[-1], 3)),
            ),
            reshape_fortran(
                sample2["hessian"].to(**dd),
                torch.Size(2 * (sample2["numbers"].shape[-1], 3)),
            ),
        ]
    )

    # variable to be differentiated
    positions.requires_grad_(True)

    hess = hessian(dftd4, (numbers, positions, charge, param), argnums=1)
    positions.detach_()

    assert pytest.approx(ref.cpu(), abs=tol, rel=tol) == hess.detach().cpu()
