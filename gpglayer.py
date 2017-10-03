import os
import gnupg
import config
import jvalidate
import sys
import contextlib
import tempfile
import atexit

_gpg_inst = None
_gpg_tempdir = None

def gpgInstance():
    global _gpg_inst
    if not _gpg_inst:
        if "pytest" in sys.modules:
            # test with GPG temp dir
            _gpg_tempdir = tempfile.TemporaryDirectory()
            atexit.register(_gpg_tempdir.cleanup)
            _gpg_inst=gnupg.GPG(gnupghome = _gpg_tempdir.name)
        else:
            gnupg_dir = os.path.join(os.getenv("HOME"),
                                     config.gnupg_directory)
            _gpg_inst = gnupg.GPG(gnupghome = gnupg_dir)
    return _gpg_inst

def sanitize_pgppubkey(pgp_pubkey):
    gpg=gpgInstance()
    ir = gpg.import_keys(pgp_pubkey)

    if not ir.count:
        raise jvalidate.ValidationError("No PGP key found in supplied PGP key data.")
