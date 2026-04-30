#
# MIT License
#
# (C) Copyright 2026 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#

"""
Context manager to suppress insecure request warnings
"""

from contextlib import AbstractContextManager
import datetime
import os
import tempfile
from types import TracebackType
from typing import Type, Union

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_self_signed_cert(cert_file_path: str, key_file_path: str) -> None:
    """
    Generate self-signed certs and write them to the specified files.
    """
    # Generate private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Build certificate subject/issuer
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "XX"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "ZZ"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Harftown"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Local Dev"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    # Build certificate
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    with open(key_file_path, "wb") as key_file:
        key_file.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(cert_file_path, "wb") as cert_file:
        cert_file.write(cert.public_bytes(serialization.Encoding.PEM))


class CertFiles(AbstractContextManager):
    """
    Context manager for the temporary certificate files
    """
    def __init__(self):
        self._cert_file: Union[str, None] = None
        self._key_file: Union[str, None] = None

    @property
    def cert_file(self) -> str:
        """
        Return the path to the cert file
        """
        assert self._cert_file is not None
        return self._cert_file

    @property
    def key_file(self) -> str:
        """
        Return the path to the key file
        """
        assert self._key_file is not None
        return self._key_file

    def __enter__(self):
        self._cert_file = tempfile.mkstemp()[1]
        self._key_file = tempfile.mkstemp()[1]
        generate_self_signed_cert(self._cert_file, self._key_file)
        return self

    def __exit__(  # pylint: disable=useless-return
            self, exc_type: Union[Type[BaseException], None],
            exc_val: Union[BaseException, None],
            exc_tb: Union[TracebackType, None]) -> Union[bool, None]:
        # Delegate cleanup to the ExitStack
        (cert_fp,
         key_fp,
         self._cert_file,
         self._key_file) = (self._cert_file,
                            self._key_file,
                            None, None)
        for fpath in [cert_fp, key_fp]:
            try:
                os.remove(fpath)
            except FileNotFoundError:
                pass 
        return None
