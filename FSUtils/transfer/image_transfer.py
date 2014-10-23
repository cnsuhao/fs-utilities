#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyleft (C) 2014 - kyle <kyle@finereport.com>
# =============================================================================
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# =============================================================================

__author__ = 'kyle'

import re

from .transfer_base import TransferBase


class ImageTransfer(TransferBase):
    _source_pattern = ["*.java", "*.js", "*.css"]

    project_root = "./"
    target_image_path = ""

    @staticmethod
    def get_source_image_path(src_file):
        with open(src_file) as src:
            codes = src.readlines()
            for line in codes:
                re.findall('com.+\.(png|jpg|gif)', line)

if __name__ == '__main__':
    trans = ImageTransfer()
