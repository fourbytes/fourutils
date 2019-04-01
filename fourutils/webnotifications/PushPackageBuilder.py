import json
import os
import zipfile
from io import BytesIO
from tempfile import TemporaryDirectory
from hashlib import sha512
import time

from PIL import Image
from OpenSSL import crypto

from ..log import make_logger


class PushPackageBuilder(object):

    def __init__(self, icon_path, website_dict, key_path, key_password=None):
        self.images = {}
        self.website_dict = website_dict
        self.build_images(icon_path)
        with open(key_path, 'rb') as f:
            key_buf = f.read()
        self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, key_buf)
        self.key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_buf)
        self.log = make_logger(__name__)

    def get_hash_details(self, data=None, sha_hash=None):
        return {
            'hashType': 'sha512',
            'hashValue': sha_hash or sha512(data).hexdigest()
        }

    def build_images(self, image_src, force=False):
        sizecats = (16, 32, 128)
        if len(self.images.values()) == sizecats * 2 and not force:
            # Use cached images.
            return
        else:
            # Reset self.images, we want to regen.
            self.images = {}

        with Image.open(image_src) as im:
            for sizecat in sizecats:
                with BytesIO() as nim_f:
                    nim = im.resize((sizecat, sizecat))
                    nim.save(nim_f, format='png')
                    self.images[f'icon_{sizecat}x{sizecat}.png'] = nim_f.getvalue()

                with BytesIO() as nim_f:
                    nim = im.resize((sizecat*2, sizecat*2))
                    nim.save(nim_f, format='png')
                    self.images[f'icon_{sizecat}x{sizecat}@2x.png'] = nim_f.getvalue()

    def build_zip(self, zf, website_dict):
        manifest = {}
        for path, data in self.images.items():
            full_path = os.path.join('icon.iconset/', path)
            zf.writestr(full_path, data)
            manifest[full_path] = self.get_hash_details(data)

        website_data = json.dumps(website_dict).encode()
        zf.writestr('website.json', website_data)
        manifest['website.json'] = self.get_hash_details(website_data)

        manifest_data = json.dumps(manifest).encode()
        zf.writestr('manifest.json', manifest_data)
        self.log.debug('Wrote manifest: %s', manifest_data)

        zf.writestr('signature', self.sign_manifest(manifest_data))

    def build_pushpackage(self, output_file=None, merge_website_dict={}):
        output_file = output_file or BytesIO()

        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            self.log.debug('Building new zip in %s', zf)
            self.build_zip(zf, website_dict={
                **self.website_dict,
                **merge_website_dict
            })
        output_file.seek(0)

        return output_file

    def sign_manifest(self, manifest_data):
        # Fuck me. Thanks @WhyNotHugo: https://stackoverflow.com/a/41553623
        bio_in = crypto._new_mem_buf(manifest_data)
        PKCS7_NOSIGS = 0x4  # defined in pkcs7.h
        pkcs7 = crypto._lib.PKCS7_sign(self.cert._x509, self.key._pkey, crypto._ffi.NULL, bio_in, PKCS7_NOSIGS)  # noqa
        bio_out = crypto._new_mem_buf()
        crypto._lib.i2d_PKCS7_bio(bio_out, pkcs7)
        sigbytes = crypto._bio_to_string(bio_out)

        return sigbytes
