import binascii
import os
import uuid
from typing import List

import aioipfs
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from sqlalchemy.orm import Session

from custody.core.config import settings
from custody.db.models.storage import Content
from custody.db.models.storage.key import Key, Secret
from custody.db.models.user import User

original_ipfs_address = settings.IPFS.ORIGINAL_IPFS_NODE_ADDRESS
encrypted_ipfs_address = settings.IPFS.ENCRYPTED_IPFS_NODE_ADDRESS


class FileEncryptor:
    def __init__(self, aes_key):
        self.aes_key = aes_key


class StorageManager:
    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db

    def add_content(self, original_cid: str, name: str) -> Content:
        content = Content(original_cid=original_cid, owner=self.user, name=name)
        self.db.add(content)
        self.db.commit()
        return content

    def get_content(self, content_id: int) -> Content:
        return (
            self.db.query(Content)
            .filter(Content.id == content_id and Content.owner_id == self.user.id)
            .first()
        )

    def list_content(self) -> List[Content]:
        return self.db.query(Content).filter(Content.owner_id == self.user.id).all()

    def list_keys(self) -> List[Key]:
        return self.db.query(Key).filter(Key.owner_id == self.user.id).all()

    def create_key(self):
        rsa_key = RSA.generate(2048)
        cipher_rsa = PKCS1_OAEP.new(rsa_key)
        secret_data = rsa_key.export_key()
        session_key = get_random_bytes(16)
        enc_session_key = cipher_rsa.encrypt(session_key)
        print(enc_session_key)

        secret = Secret(data=secret_data)
        key = Key(
            kind="rsa",
            aes_key=binascii.b2a_base64(enc_session_key).decode("utf-8").strip(),
            secret=secret,
            owner=self.user,
        )
        self.db.add(secret)
        self.db.add(key)
        self.db.commit()
        return key

    async def process_encryption(self, original_cid, aes_key):
        file_path = f"./tmp/{uuid.uuid4()}"
        file_out = open(file_path, "wb")

        key = (
            self.db.query(Key)
            .filter(Key.aes_key == aes_key, Key.owner_id == self.user.id)
            .first()
        )
        secret = key.secret
        print(key.aes_key)
        recipient_key = RSA.import_key(secret.data)
        cipher_rsa = PKCS1_OAEP.new(recipient_key)

        aes_key_binary = binascii.a2b_base64(key.aes_key)
        session_key = cipher_rsa.decrypt(aes_key_binary)
        enc_session_key = aes_key_binary
        cipher_aes = AES.new(session_key, AES.MODE_EAX)
        print("start getting data")
        async with aioipfs.AsyncIPFS(host=original_ipfs_address, port=5001) as client:
            res = await client.cat(original_cid)
            print("content got")

        async with aioipfs.AsyncIPFS(host=encrypted_ipfs_address, port=5001) as client:

            ciphertext, tag = cipher_aes.encrypt_and_digest(res)
            [
                file_out.write(x)
                for x in (enc_session_key, cipher_aes.nonce, tag, ciphertext)
            ]
            file_out.close()
            print("file encrypted")
            encrypted_info = [entry async for entry in client.add(file_path)][0]
            os.remove(file_path)
        encrypted_cid = encrypted_info["Hash"]
        encrypted_size = encrypted_info["Size"]
        content = Content(
            original_cid=original_cid,
            name=original_cid,
            encrypted_cid=encrypted_cid,
            encrypted_size=encrypted_size,
            owner=self.user,
            key_id=key.id,
        )
        self.db.add(content)
        self.db.commit()
        self.db.close()
        print("content encryption finished")

        result = {
            "original_cid": original_cid,
            "aes_key": aes_key,
            "encrypted_cid": encrypted_cid,
            "encrypted_size": encrypted_size,
        }
        return result

    async def process_decryption(self, original_cid, aes_key):
        key = (
            self.db.query(Key)
            .filter(Key.aes_key == aes_key, Key.owner_id == self.user.id)
            .first()
        )
        content = (
            self.db.query(Content)
            .filter(Content.original_cid == original_cid, Content.key_id == key.id)
            .first()
        )
        secret = key.secret
        print(key.aes_key)
        recipient_key = RSA.import_key(secret.data)
        cipher_rsa = PKCS1_OAEP.new(recipient_key)

        aes_key_binary = binascii.a2b_base64(key.aes_key)
        session_key = cipher_rsa.decrypt(aes_key_binary)
        async with aioipfs.AsyncIPFS(host=original_ipfs_address, port=5001) as client:
            file_path = f"./tmp/{uuid.uuid4()}"
            res = await client.cat(content.encrypted_cid)
            print("content got")
            with open(file_path, "wb") as f:
                f.write(res)

            file_in = open(file_path, "rb")
            enc_session_key, nonce, tag, ciphertext = [
                file_in.read(x) for x in (recipient_key.size_in_bytes(), 16, 16, -1)
            ]

            cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)

            data = cipher_aes.decrypt_and_verify(ciphertext, tag)
            print("content decrypted")
            with open(file_path, "wb") as f:
                f.write(data)
            original_cid = [entry["Hash"] async for entry in client.add(file_path)][0]
            os.remove(file_path)
            print(f"content {original_cid} decryption finished")

            result = {
                "encrypted_cid": content.encrypted_cid,
                "aes_key": aes_key,
                "original_cid": original_cid,
            }
            return result

    async def get_content_data(self, content: Content):
        client = aioipfs.AsyncIPFS(maddr=original_ipfs_address)
        result_data = await client.cat(content.original_cid)

        return result_data
