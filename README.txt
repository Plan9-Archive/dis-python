Dis Virtual Machine Tools for Python
====================================

Introduction
------------

This package contains Python modules for reading and writing files for the Dis
virtual machine[1], used by the Inferno operating system[2]. Although the aim
of these modules was to create a toolchain for producing .dis files, they are
more useful for reading existing ones.

Reading a .dis File
-------------------

Sample .dis files are not provided, but you can compile the Limbo source code
files from the Tests/Limbo directory to obtain simple .dis files to inspect.
This is done using the limbo compiler supplied with Inferno.

From within the package directory, or with the directory on the PYTHONPATH,
you can run the Python interpreter and inspect the contents of an existing .dis
file in the following way:

  import dis
  d = dis.Dis()
  d.read(open("/tmp/countmin.dis"), "countmin.dis")
  d.list()

For the compiled version of the countmin.b file, the Python should produce
output similar to the following:

  0x0: load 0(mp), $0x0, 48(fp)
  0x1: movw $0x0, 40(fp)
  0x2: blew $0x7b, 40(fp), $0x5
  0x3: addw $0x1, 40(fp)
  0x4: jmp $0x2
  0x5: ret 

  entry 0x0, 1
  desc $0x0, 8, "c0"
  desc $0x1, 56, "00c8"

  var @mp, 8
  string @mp+0, "$Sys"

  module count

  link 0x0, 1, 0x4244b354, "init"

  ldts @ldt, 0

  source "/tmp/countmin.b"

The location of the source file when it was compiled by the limbo compiler will
influence the value presented in the output of the list() method.

Tests
-----

Some tests that write .dis files are included in the Tests directory. These
will try to create the corresponding .dis files to their equivalent Limbo
programs. Ensure that the package directory is on the PYTHONPATH and run them
in the following way:

  PYTHONPATH=. ./Tests/countmin.py /tmp/countmin.dis

You should then be able to run them in the Inferno emulator and inspect them
using the method described in the previous section.

Authors and License
-------------------

David Boddie <david@boddie.org.uk>

Unless indicated otherwise, the contents of this package are licensed under the
GNU General Public License version 3 (or later).

  Copyright (C) 2017 David Boddie <david@boddie.org.uk>

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

References
----------

[1] http://inferno-os.org/inferno/papers/dis.html
[2] http://inferno-os.org
[3] http://inferno-os.org/inferno/papers/limbo.html
