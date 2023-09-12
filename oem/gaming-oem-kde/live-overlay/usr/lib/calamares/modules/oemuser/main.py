#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# === This file is part of Calamares - <http://github.com/calamares> ===
#
#   Copyright 2017-2021, Philip Müller <philm@manjaro.org>
#
#   Calamares is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Calamares is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Calamares. If not, see <http://www.gnu.org/licenses/>.

import libcalamares

import os
import logging
import crypt
from os.path import join, exists
from distutils.dir_util import copy_tree
from libcalamares.utils import target_env_call


class ConfigOem:
    def __init__(self):
        self.__root = libcalamares.globalstorage.value("rootMountPoint")
        self.__groups = 'video,audio,power,disk,storage,optical,network,lp,scanner,wheel,autologin'
        libcalamares.globalstorage.insert("autoLoginUser", "gamer")
        libcalamares.globalstorage.insert("username", "gamer")

    @property
    def root(self):
        return self.__root

    @property
    def groups(self):
        return self.__groups

    @staticmethod
    def change_user_password(user, new_password):
        """ Changes the user's password """
        try:
            shadow_password = crypt.crypt(new_password, crypt.mksalt(crypt.METHOD_SHA512))
        except:
            logging.warning(_("Error creating password hash for user {0}".format(user)))
            return False

        try:
            target_env_call(['usermod', '-p', shadow_password, user])
        except:
            logging.warning(_("Error changing password for user {0}".format(user)))
            return False

        return True

    def remove_symlink(self, target):
        for root, dirs, files in os.walk("/" + target):
            for filename in files:
                path = os.path.join(root, filename)
                if os.path.islink(path):
                    os.unlink(path)

    def copy_folder(self, source, target):
        if exists("/" + source):
            copy_tree("/" + source, join(self.root, target), preserve_symlinks=1)

    def run(self):
        target_env_call(['groupadd', 'autologin'])
        target_env_call(['mv', '/etc/skel', '/etc/skel_'])
        target_env_call(['mv', '/etc/oemskel', '/etc/skel'])
        target_env_call(['useradd', '-m', '-s', '/bin/bash', '-U', '-G', self.groups, 'gamer'])
        target_env_call(['mv', '/etc/skel', '/etc/oemskel'])
        target_env_call(['mv', '/etc/skel_', '/etc/skel'])
        self.change_user_password('gamer', 'gamer')
        path = os.path.join(self.root, "etc/sudoers.d/g_gamer")
        with open(path, "w") as oem_file:
            oem_file.write("gamer ALL=(ALL) NOPASSWD: ALL")

        # Remove symlinks before copying   
        self.remove_symlink('root')

        # Copy skel to root
        self.copy_folder('etc/skel', 'root')

        # Enable 'menu_auto_hide' when supported in grubenv
        if exists(join(self.root, "usr/bin/grub-set-bootflag")):
            target_env_call(["grub-editenv", "-", "set", "menu_auto_hide=1", "boot_success=1"])

        # Remove unneeded ucode
        cpu_ucode = target_env_call(["hwinfo", "--cpu", "|", "grep", "Vendor:", "-m1", "|", "cut", "-d\'\"\'", "-f2"])
        if cpu_ucode == "AuthenticAMD":
            self.remove_pkg("intel-ucode", "boot/intel-ucode.img")
        elif cpu_ucode == "GenuineIntel":
            self.remove_pkg("amd-ucode", "boot/amd-ucode.img")

        return None


def run():
    """ Set OEM User """

    oem = ConfigOem()

    return oem.run()
