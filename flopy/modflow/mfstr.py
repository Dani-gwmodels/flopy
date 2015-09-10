"""
mfstr module.  Contains the ModflowStr class. Note that the user can access
the ModflowStr class as `flopy.modflow.ModflowStr`.

Additional information for this MODFLOW package can be found at the `Online
MODFLOW Guide
<http://water.usgs.gov/ogw/modflow/MODFLOW-2005-Guide/str.htm>`_.

"""
import sys
import numpy as np
from flopy.mbase import Package
from flopy.utils.util_list import mflist


class ModflowStr(Package):
    """
    MODFLOW Stream Package Class.

    Parameters
    ----------
    model : model object
        The model object (of type :class:`flopy.modflow.mf.Modflow`) to which
        this package will be added.
    ipakcb : int
        is a flag and a unit number. (the default is 0).
    stress_period_data : list of boundaries or
                         recarray of boundaries or
                         dictionary of boundaries
        Each river cell is defined through definition of
        layer (int), row (int), column (int), stage (float), cond (float),
        rbot (float).
        The simplest form is a dictionary with a lists of boundaries for each
        stress period, where each list of boundaries itself is a list of
        boundaries. Indices of the dictionary are the numbers of the stress
        period. This gives the form of
            stress_period_data =
            {0: [
                [lay, row, col, stage, cond, rbot],
                [lay, row, col, stage, cond, rbot],
                [lay, row, col, stage, cond, rbot]
                ],
            1:  [
                [lay, row, col, stage, cond, rbot],
                [lay, row, col, stage, cond, rbot],
                [lay, row, col, stage, cond, rbot]
                ], ...
            kper:
                [
                [lay, row, col, stage, cond, rbot],
                [lay, row, col, stage, cond, rbot],
                [lay, row, col, stage, cond, rbot]
                ]
            }

        Note that if the number of lists is smaller than the number of stress
        periods, then the last list of rivers will apply until the end of the
        simulation. Full details of all options to specify stress_period_data
        can be found in the flopy3 boundaries Notebook in the basic
        subdirectory of the examples directory.
    options : list of strings
        Package options. (default is None).
    naux : int
        number of auxiliary variables
    extension : string
        Filename extension (default is 'riv')
    unitnumber : int
        File unit number (default is 18).

    Attributes
    ----------
    mxactr : int
        Maximum number of river cells for a stress period.  This is calculated
        automatically by FloPy based on the information in
        layer_row_column_data.

    Methods
    -------

    See Also
    --------

    Notes
    -----
    Parameters are not supported in FloPy.

    Examples
    --------

    >>> import flopy
    >>> m = flopy.modflow.Modflow()
    >>> lrcd = {}
    >>> lrcd[0] = [[2, 3, 4, 15.6, 1050., -4]]  #this river boundary will be
    >>>                                         #applied to all stress periods
    >>> str8 = flopy.modflow.ModflowStr(m, stress_period_data=lrcd)

    """

    def __init__(self, model, ipakcb=0, stress_period_data=None, dtype=None,
                 extension='str', unitnumber=118, options=None, **kwargs):
        """
        Package constructor.

        """
        # Call parent init to set self.parent, extension, name and unit number
        Package.__init__(self, model, extension, 'STR', unitnumber)
        self.heading = '# STR for MODFLOW, generated by Flopy.'
        self.url = 'str.htm'
        self.ipakcb = ipakcb
        self.mxactr = 0
        self.np = 0
        if options is None:
            options = []
        self.options = options
        if dtype is not None:
            self.dtype = dtype
        else:
            self.dtype = self.get_default_dtype(structured=self.parent.structured)
        #self.stress_period_data = mflist(model, self.dtype, stress_period_data)
        self.stress_period_data = mflist(self, stress_period_data)
        self.parent.add_package(self)

    def __repr__(self):
        return 'River class'

    @staticmethod
    def get_empty(ncells=0, aux_names=None, structured=True):
        # get an empty recarray that correponds to dtype
        dtype = ModflowStr.get_default_dtype(structured=structured)
        if aux_names is not None:
            dtype = Package.add_to_dtype(dtype, aux_names, np.float32)
        d = np.zeros((ncells, len(dtype)), dtype=dtype)
        d[:, :] = -1.0E+10
        return np.core.records.fromarrays(d.transpose(), dtype=dtype)

    @staticmethod
    def get_default_dtype(structured=True):
        if structured:
            dtype = np.dtype([("k", np.int), ("i", np.int), ("j", np.int),
                              ("segment", np.int), ("reach", np.int),
                              ("flow", np.float32), ("stage", np.float32),
                              ("cond", np.float32), ("sbot", np.float32),
                              ("stop", np.float32)])
        else:
            dtype = np.dtype([("node", np.int),
                              ("segment", np.int), ("reach", np.int),
                              ("flow", np.float32), ("stage", np.float32),
                              ("cond", np.float32), ("sbot", np.float32),
                              ("stop", np.float32)])

        return dtype

    def ncells(self):
        # Return the  maximum number of cells that have river
        # (developed for MT3DMS SSM package)
        return self.stress_period_data.mxact

    def write_file(self):
        """
        Write the file.

        """
        f_str = open(self.fn_path, 'w')
        f_str.write('{0}\n'.format(self.heading))
        line = '{0:10d}{1:10d}'.format(self.stress_period_data.mxact, self.ipakcb)
        for opt in self.options:
            line += ' ' + str(opt)
        line += '\n'
        f_str.write(line)
        self.stress_period_data.write_transient(f_str)
        f_str.close()

    def add_record(self, kper, index, values):
        try:
            self.stress_period_data.add_record(kper, index, values)
        except Exception as e:
            raise Exception("mfriv error adding record to list: " + str(e))

    @staticmethod
    def load(f, model, nper=None, ext_unit_dict=None):
        """
        Load an existing package.

        Parameters
        ----------
        f : filename or file handle
            File to load.
        model : model object
            The model object (of type :class:`flopy.modflow.mf.Modflow`) to
            which this package will be added.
        nper : int
            The number of stress periods.  If nper is None, then nper will be
            obtained from the model object. (default is None).
        ext_unit_dict : dictionary, optional
            If the arrays in the file are specified using EXTERNAL,
            or older style array control records, then `f` should be a file
            handle.  In this case ext_unit_dict is required, which can be
            constructed using the function
            :class:`flopy.utils.mfreadnam.parsenamefile`.

        Returns
        -------
        str : ModflowStr object
            ModflowStr object.

        Examples
        --------

        >>> import flopy
        >>> m = flopy.modflow.Modflow()
        >>> strm = flopy.modflow.ModflowStr.load('test.str', m)

        """

        if model.verbose:
            sys.stdout.write('loading str package file...\n')

        if not hasattr(f, 'read'):
            filename = f
            f = open(filename, 'r')

        # dataset 0 -- header
        while True:
            line = f.readline()
            if line[0] != '#':
                break

        # read dataset 1 - optional parameters
        npstr, mxl = 0, 0
        t = line.strip().split()
        if t[0].lower() == 'parameter':
            if model.verbose:
                sys.stdout.write('  loading str dataset 1\n')
            npstr = int(t[1])
            mxl = int(t[2])

            # read next line
            line = f.readline()

        # data set 2
        if model.verbose:
            sys.stdout.write('  loading str dataset 2\n')
        t = line.strip().split()
        mxacts = int(t[0])
        nss = int(t[1])
        ntrib = int(t[2])
        ndiv = int(t[3])
        icalc = int(t[4])
        const = float(t[5])
        istcb1 = int(t[6])
        istcb2 = int(t[7])
        ipakcb = 0
        try:
            if istcb1 != 0:
                ipakcb = 53
                model.add_pop_key_list(istcb1)
        except:
            pass
        try:
            if istcb2 != 0:
                ipakcb = 53
                model.add_pop_key_list(istcb2)
        except:
            pass

        options = []
        aux_names = []
        if len(t) > 8:
            it = 8
            while it < len(t):
                toption = t[it]
                if 'aux' in toption.lower():
                    options.append(' '.join(t[it:it + 2]))
                    aux_names.append(t[it + 1].lower())
                    it += 1
                it += 1

        # read parameter data
        if npstr > 0:
            dt = ModflowStr.get_empty(1, aux_names=aux_names).dtype
            pak_parms = mfparbc.load(f, npstr, dt, model.verbose)

        if nper is None:
            nrow, ncol, nlay, nper = model.get_nrow_ncol_nlay_nper()

        stress_period_data = {}
        ds8 = {}
        ds9 = {}
        ds10 = {}
        for iper in range(nper):
            if model.verbose:
                print("   loading " + str(ModflowStr) + " for kper {0:5d}".format(iper + 1))
            line = f.readline()
            if line == '':
                break
            t = line.strip().split()
            itmp = int(t[0])
            irdflg, iptflg = 0, 0
            if len(t) > 1:
                irdflg = int(t[1])
            if len(t) > 2:
                iptflg = int(t[2])

            if itmp == 0:
                bnd_output = None
                current = ModflowStr.get_empty(itmp, aux_names=aux_names)
            elif itmp > 0:
                if npstr > 0:
                    partype = ['cond']
                    for iparm in range(itmp):
                        line = f.readline()
                        t = line.strip().split()
                        pname = t[0].lower()
                        iname = 'static'
                        try:
                            tn = t[1]
                            c = tn.lower()
                            instance_dict = pak_parms.bc_parms[pname][1]
                            if c in instance_dict:
                                iname = c
                            else:
                                iname = 'static'
                        except:
                            pass
                        par_dict, current_dict = pak_parms.get(pname)
                        data_dict = current_dict[iname]

                        current = ModflowStr.get_empty(par_dict['nlst'], aux_names=aux_names)

                        #  get appropriate parval
                        if model.mfpar.pval is None:
                            parval = np.float(par_dict['parval'])
                        else:
                            try:
                                parval = np.float(model.mfpar.pval.pval_dict[pname])
                            except:
                                parval = np.float(par_dict['parval'])

                        # fill current parameter data (par_current)
                        for ibnd, t in enumerate(data_dict):
                            current[ibnd] = tuple(t[:len(current.dtype.names)])

                else:
                    current = ModflowStr.get_empty(itmp, aux_names=aux_names)
                    for ibnd in range(itmp):
                        line = f.readline()
                        if "open/close" in line.lower():
                            #raise NotImplementedError("load() method does not support \'open/close\'")
                            oc_filename = os.path.join(model.model_ws, line.strip().split()[1])
                            assert os.path.exists(oc_filename), "Package.load() error: open/close filename " + \
                                                                oc_filename + " not found"
                            try:
                                current = np.genfromtxt(oc_filename, dtype=current.dtype)
                                current = current.view(np.recarray)
                            except Exception as e:
                                raise Exception("Package.load() error loading open/close file " + oc_filename + \
                                                " :" + str(e))
                            assert current.shape[0] == itmp, "Package.load() error: open/close rec array from file " + \
                                                             oc_filename + " shape (" + str(current.shape) + \
                                                             ") does not match itmp: {0:d}".format(itmp)
                            break
                        try:
                            t = line.strip().split()
                            current[ibnd] = tuple(t[:len(current.dtype.names)])
                        except:
                            t = []
                            ipos = [5, 5, 5, 5, 5, 15, 10, 10, 10, 10]
                            istart = 0
                            for ivar in range(len(ipos)):
                                istop = istart + ipos(ivar)
                                t.append(line[istart:istop])
                                istart = istop + 1
                            if len(aux_names) > 0:
                                tt = line[istart:].strip().split()
                                for ivar in len(aux_names):
                                    t.append(tt[ivar])
                            current[ibnd] = tuple(t[:len(current.dtype.names)])

                # convert indices to zero-based
                current['k'] -= 1
                current['i'] -= 1
                current['j'] -= 1
                bnd_output = np.recarray.copy(current)

                # read dataset 8
                if icalc > 0:
                    tds8 = np.zeros((itmp, 3), dtype=np.float)
                    for ibnd in range(itmp):
                        line = f.readline()
                        try:
                            t = line.strip().split()
                            v1, v2, v3 = float(t[0]), float(t[1]), float(t[2])
                        except:
                            t = []
                            ipos = [10, 10, 10]
                            istart = 0
                            for ivar in range(len(ipos)):
                                istop = istart + ipos(ivar)
                                t.append(line[istart:istop])
                                istart = istop + 1
                            v1, v2, v3 = float(t[0]), float(t[1]), float(t[2])
                        tds8[ibnd, :] = v1, v2, v3


            else:
                bnd_output = np.recarray.copy(current)



            if bnd_output is None:
                stress_period_data[iper] = itmp
            else:
                stress_period_data[iper] = bnd_output


        str8 = None
        return str8
