# Thin wrapper around GPG and Vitalik's bitcoin lib
# for action signature verification
import tempfile
import bitcoin
import gnupg
import logging
import config
import gpglayer
from tmember import Member
import jvalidate
log=logging.getLogger(__name__)


def checkSig(message, signature, authorname):
    """ Checks that message has a valid, detached signature "signature",
    given authorname. For any mismatch found, create a corresponding
    jvalidate.ValidationError(...) exception. """

    if not isinstance(message, bytes):
        message = message.encode("ascii")
        
    if not isinstance(signature, bytes):
        signature = signature.encode("ascii")

    if config.disable_signature_checking:
        # signature checking disabled for testing
        log.warn("Signature check disable in config: %s, %s, %s" % (message, signature, authorname))
        return
    
    if b"PGP SIGNATURE" in signature:
        checkSigGPG(message, signature, authorname)
    else:
        checkSigBitcoin(message, signature, authorname)
        
def checkSigBitcoin(message, signature, authorname):
    try:
        # FIXME: is base64.b64decode(...) safe?
        pub=bitcoin.ecdsa_recover(message, signature)
    except:
        raise jvalidate.ValidationError("Bitcoin signature or message invalid.")
    author = Member.by_name(authorname)

    if author is None:
        raise jvalidate.ValidationError("Member '%s' not found for PGP signature check." % authorname)
    
    addr = author.address
    addr_from_pub = bitcoin.pubkey_to_address(pub)
    # is this enough? FIXME: review!
    # FIXME: check type(?) bug in bitcoin.ecsda_verify_addr

    if addr != addr_from_pub:
        raise jvalidate.ValidationError(
                    "Bitcoin signature validation failed (%s, %s, %s)." % (repr(message), signature, addr))

    
def checkSigGPG(message, signature, authorname):
    gpg = gpglayer.gpgInstance()

    author = Member.by_name(authorname)

    if author is None:
        raise jvalidate.ValidationError("Member '%s' not found for PGP signature check." % authorname)

    if author.pgp_pubkey is None:
        raise jvalidate.ValidationError(
            "PGP-signed message for author %s, but author has no PGP public key entered." % authorname)

    import_result = gpg.import_keys(author.pgp_pubkey)

    if not len(import_result.fingerprints):
        raise jvalidate.ValidationError(
            "Message author %s has no valid PGP key data." % authorname)

    # python-GnuPG seems to like either the sig or the file to be on disk,
    # so that's the reason for this convoluted approach here:
    with tempfile.NamedTemporaryFile() as sigfile:
        sigfile.write(signature)
        sigfile.flush()

        verification = gpg.verify_data(sigfile.name, message)

        if not verification.valid:
            raise jvalidate.ValidationError(
                "GPG signature invalid: %s, %s" % (signature, message))

        # FIXME: review this. Is that always the correct spot to look
        # for the fingerprint? Can an attacker change the order in the import
        # to fake something here?
        if verification.fingerprint != import_result.fingerprints[0]:
            raise jvalidate.ValidationError(
                "GPG signature uses wrong key: %s, %s (%s vs. %s)" % (
                    signature, message,
                    verification.fingerprint,
                    import_result.fingerprints[0]))


# FIXME: exclude md5/sha1 signed messages
