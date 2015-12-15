"""Deals with testing the io system.

Note that this will only run if you have Python version 2.5 or later.
Otherwise, replace all the with statements with f = filestream.
"""

# This file is part of i-PI.
# i-PI Copyright (C) 2014-2015 i-PI developers
# See the "licenses" directory for full license information.


import filecmp
import os

import numpy as np
from numpy.testing import assert_equal

from common import local
from ipi.utils.io import iter_file, read_file, print_file


pos = np.array([i for i in range(3*3)])


def test_read_xyz():
    """Tests that xyz files are read correctly."""

    with open(local("test.pos_0.xyz"), "r") as f:
        ret = read_file("xyz", f)
        atoms = ret["atoms"]
        assert len(atoms) == 3
        assert_equal(pos, atoms.q)


def test_iter_xyz():
    """Tests that xyz files with multiple frames are read correctly."""

    with open(local("test.pos_0.xyz"), "r") as f:
        for num, ret in enumerate(iter_file("xyz", f)):
            atoms = ret["atoms"]
            assert len(atoms) == 3
            assert_equal(pos*(num+1), atoms.q)


def test_read_pdb():
    """Tests that pdb files are read correctly."""

    with open(local("test.pos_0.pdb"), "r") as f:
        ret = read_file("pdb", f)
        atoms = ret["atoms"]
        assert len(atoms) == 3
        assert_equal(pos, atoms.q)
        # TODO: test cell


def test_iter_pdb():
    """Tests that pdb files with multiple frames are read correctly."""

    with open(local("test.pos_0.pdb"), "r") as f:
        for num, ret in enumerate(iter_file("pdb", f)):
            atoms = ret["atoms"]
            assert len(atoms) == 3
            assert_equal(pos*(num+1), atoms.q)


def test_print_pdb2xyz():
    """Tests that pdb->xyz files are printed correctly."""

    with open(local("test.pos_0.pdb"), "r") as f:
        with open(local("test.pos_1.xyz"), "w") as out:
            for num, ret in enumerate(iter_file("pdb", f)):
                atoms = ret["atoms"]
                assert len(atoms) == 3
                assert_equal(pos*(num+1), atoms.q)
                print_file("xyz", atoms, ret["cell"], filedesc=out,
                           title=ret["comment"])

    assert filecmp.cmp(local("test.pos_0.xyz"), local("test.pos_1.xyz"))
    os.unlink(local("test.pos_1.xyz"))


def test_print_pdb2pdb():
    """Tests that pdb->pdb files are printed correctly."""

    with open(local("test.pos_0.pdb"), "r") as f:
        with open(local("test.pos_1.pdb"), "w") as out:
            for num, ret in enumerate(iter_file("pdb", f)):
                atoms = ret["atoms"]
                assert len(atoms) == 3
                assert_equal(pos*(num+1), atoms.q)
                print_file("pdb", atoms, ret["cell"], filedesc=out,
                           title=ret["comment"])

    assert filecmp.cmp(local("test.pos_0.pdb"), local("test.pos_1.pdb"))
    os.unlink(local("test.pos_1.pdb"))


def test_read_xyz2():
    """Tests that mode/xyz files are read correctly."""

    with open(local("test.pos_0.xyz"), "r") as f:
        ret = read_file("xyz", f)
        atoms = ret["atoms"]
        assert len(atoms) == 3
        assert_equal(pos, atoms.q)


def test_iter_xyz2():
    """Tests that mode/xyz files with multiple frames are read correctly."""

    with open(local("test.pos_0.xyz"), "r") as f:
        for num, ret in enumerate(iter_file("xyz", f)):
            atoms = ret["atoms"]
            assert len(atoms) == 3
            assert_equal(pos*(num+1), atoms.q)


def test_read_pdb2():
    """Tests that mode/pdb files are read correctly."""

    with open(local("test.pos_0.pdb"), "r") as f:
        ret = read_file("pdb", f)
        atoms = ret["atoms"]
        assert len(atoms) == 3
        assert_equal(pos, atoms.q)
        # TODO: test cell


def test_iter_pdb2():
    """Tests that mode/pdb files with multiple frames are read correctly."""

    with open(local("test.pos_0.pdb"), "r") as f:
        for num, ret in enumerate(iter_file("pdb", f)):
            atoms = ret["atoms"]
            assert len(atoms) == 3
            assert_equal(pos*(num+1), atoms.q)
