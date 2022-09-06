# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# NOTE: This package is new and has been tested on a limited set of use cases:
# Arm archs: Graviton 2, Graviton 3
# Compilers: Gcc 12.1.0, Arm 22.0.1, NVHPC 22.3 

from spack.package import *

class MgcfdOp2(MakefilePackage):
    """Package for the OP2 port of MGCFD: A 3D unstructured multigrid, finite-volume computational fluid dynamics (CFD) mini-app for inviscid-flow."""

    homepage = "https://github.com/warwick-hpsc/MG-CFD-app-OP2"
    git = "https://github.com/warwick-hpsc/MG-CFD-app-OP2.git"

    maintainers = ['rob64j', 'tomdeakin']

    version('v1.0.0-rc1')

    variant('mpi', default=False, description="Enable MPI support")

    depends_on('gmake@4.3')
    # KaHIP is a new MGCFD-OP2 dependency and NVHPC builds require the latest develop branch at time of writing (Sept 22)
    depends_on('kahip@develop+metis', when='+mpi')
    depends_on('op2-dsl+mpi', when='+mpi')
    depends_on('op2-dsl~mpi', when='~mpi')
    
    def edit(self, spec, prefix):
        compiler_map = {
            'gcc': 'gnu',
            'arm': 'clang',
            'cce': 'cray',
            'nvhpc': 'pgi',
        }
        
        if self.spec.compiler.name in compiler_map:
            env['COMPILER'] = compiler_map[self.spec.compiler.name]
        else:
            env['COMPILER'] = self.spec.compiler.name

        # Makefile tweaks to ensure the correct compiler commands are called. 
        makefile = FileFilter('Makefile')
        if self.spec.compiler.name == 'arm':
            makefile.filter(r'CPP := clang', r'CPP := armclang')
            makefile.filter(r'-cxx=clang.*', '')

        if self.spec.compiler.name == 'nvhpc':
            makefile.filter('pgc', 'nvc')

        # This overrides a flag issue in downstream OP2. 
        if self.spec.compiler.name == 'nvhpc':
           env['CFLAGS'] = "-O3 -DOMPI_SKIP_MPICXX -DMPICH_IGNORE_CXX_SEEK -DMPIPP_H"

        # OP2 doesn't support flang/armflang fortran compiling.
        if self.spec.compiler.name == 'arm':
            env['OP2_F_COMPILER'] = 'gnu'


    def get_builds(self):
        if '+mpi' in self.spec:
            builds = ['mpi', 'mpi_vec', 'mpi_openmp']
            if '+cuda' in self.spec and spec.variants['cuda_arch'].value[0] != 'none':
                builds.append('mpi_cuda')
        else:
            builds = ['seq', 'openmp']
            if '+cuda' in self.spec and spec.variants['cuda_arch'].value[0] != 'none':
                builds.append('cuda')
        return builds

    def build(self, spec, prefix):
        for b in self.get_builds():
            make('clean_' + b)
            make(b)

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        install_tree('bin', prefix.bin)

