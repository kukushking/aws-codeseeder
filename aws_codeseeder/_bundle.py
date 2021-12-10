#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License").
#    You may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import glob
import json
import os
import shutil
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple

from aws_codeseeder import LOGGER, create_output_dir


def _is_valid_image_file(file_path: str) -> bool:
    for word in ("/build/", "/.mypy_cache/", ".egg-info", "__pycache__", "codeseeder.out", "/dist/", "/node_modules/"):
        if word in file_path:
            return False
    return True


def _list_files(path: str) -> List[str]:
    path = os.path.join(path, "**")
    return [f for f in glob.iglob(path, recursive=True) if os.path.isfile(f) and _is_valid_image_file(file_path=f)]


def generate_dir(out_dir: str, dir: str, name: str) -> str:
    absolute_dir = os.path.realpath(dir)
    final_dir = os.path.realpath(os.path.join(out_dir, name))
    LOGGER.debug("absolute_dir: %s", absolute_dir)
    LOGGER.debug("final_dir: %s", final_dir)
    os.makedirs(final_dir, exist_ok=True)
    shutil.rmtree(final_dir)

    LOGGER.debug("Copying files to %s", final_dir)
    files: List[str] = _list_files(path=absolute_dir)
    if len(files) == 0:
        raise ValueError(f"{name} ({absolute_dir}) is empty!")
    for file in files:
        LOGGER.debug(f"***file={file}")
        relpath = os.path.relpath(file, absolute_dir)
        new_file = os.path.join(final_dir, relpath)
        LOGGER.debug("Copying file to %s", new_file)
        os.makedirs(os.path.dirname(new_file), exist_ok=True)
        LOGGER.debug("Copying file to %s", new_file)
        shutil.copy(src=file, dst=new_file)

    return final_dir


def generate_bundle(
    fn_args: Dict[str, Any],
    dirs: Optional[List[Tuple[str, str]]] = None,
    files: Optional[List[Tuple[str, str]]] = None,
    bundle_id: Optional[str] = None,
) -> str:
    bundle_dir = create_output_dir(f"{bundle_id}/bundle") if bundle_id else create_output_dir("bundle")
    remote_dir = os.path.dirname(bundle_dir)

    fn_args_file = os.path.join(bundle_dir, "fn_args.json")
    LOGGER.debug("writing fn_ars file %s", fn_args_file)
    with open(fn_args_file, "w") as file:
        file.write(json.dumps(fn_args))

    LOGGER.debug(f"generate_bundle dirs={dirs}")
    # Extra Directories
    if dirs is not None:
        for dir, name in dirs:
            LOGGER.debug(f"***dir={dir}:name={name}")
            generate_dir(out_dir=bundle_dir, dir=dir, name=name)

    if files is not None:
        for src_file, name in files:
            LOGGER.debug(f"***file={src_file}:name={name}")
            shutil.copy(src=src_file, dst=os.path.realpath(os.path.join(bundle_dir, name)))

    LOGGER.debug("bundle_dir: %s", bundle_dir)

    files_glob = glob.glob(bundle_dir + "/**", recursive=True)
    LOGGER.debug("files:\n%s", pformat(files_glob))

    shutil.make_archive(base_name=bundle_dir, format="zip", root_dir=remote_dir, base_dir="bundle")
    return bundle_dir + ".zip"