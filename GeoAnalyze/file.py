import os
import shutil


class File:

    '''
    Functionality for file operations.
    '''

    def delete_by_name(
        self,
        folder_path: str,
        file_names: list[str]
    ) -> list[str]:

        '''
        Delete files of the same name irrespective of extensions and
        return a list o deleted file names.

        Parameters
        ----------
        folder_path : str
            Path of the input folder containing the files to delete.

        file_names : list
            List of file names (without extension) to delete.

        Returns
        -------
        list
            A list of file names that were deleted.
        '''

        folder_contents = map(
            lambda x: os.path.join(folder_path, x), os.listdir(folder_path)
        )

        file_paths = filter(
            lambda x: os.path.isfile(x), folder_contents
        )

        delete_paths = filter(
            lambda x: os.path.split(x)[-1].split('.')[0] in file_names, file_paths
        )

        delete_files = list(
            map(
                lambda x: os.path.split(x)[-1], delete_paths
            )
        )

        for file in delete_files:
            os.remove(
                os.path.join(folder_path, file)
            )

        return delete_files

    def transfer_by_name(
        self,
        src_folder: str,
        dst_folder: str,
        file_names: list[str]
    ) -> list[str]:

        '''
        Transfer files of the same name irrespective of extensions from
        the source folder to the destination folder.

        Parameters
        ----------
        src_folder : str
            Path of the source folder containing the files to transfer.

        dst_folder : str
            Path of the destination folder for the transferred files.

        file_names : list
            List of file names (without extension) to transfer.

        Returns
        -------
        list
            A list of file names that were transferred.
        '''

        if src_folder != dst_folder:
            pass
        else:
            raise Exception('Source and destination folders must be different.')

        src_contents = map(
            lambda x: os.path.join(src_folder, x), os.listdir(src_folder)
        )

        src_paths = filter(
            lambda x: os.path.isfile(x), src_contents
        )

        transfer_paths = filter(
            lambda x: os.path.split(x)[-1].split('.')[0] in file_names, src_paths
        )

        transfer_files = list(
            map(
                lambda x: os.path.split(x)[-1], transfer_paths
            )
        )

        for file in transfer_files:
            shutil.copy2(
                os.path.join(src_folder, file), os.path.join(dst_folder, file)
            )

        return transfer_files

    def name_change(
        self,
        folder_path: str,
        rename_map: dict[str, str]
    ) -> dict[str, str]:

        '''
        Rename files in the folder according to the provided mapping.

        Parameters
        ----------
        folder_path : str
            Path of the folder containing the files to rename.

        rename_map : dict
            Dictionary mapping old file names (without extension) to new file names.

        Returns
        -------
        dict
             A dictionary mapping old file names to new file names, with their extensions.
        '''

        folder_contents = map(
            lambda x: os.path.join(folder_path, x), os.listdir(folder_path)
        )

        file_paths = filter(
            lambda x: os.path.isfile(x), folder_contents
        )

        rename_paths = filter(
            lambda x: os.path.split(x)[-1].split('.')[0] in rename_map, file_paths
        )

        rename_files = list(
            map(
                lambda x: os.path.split(x)[-1], rename_paths
            )
        )

        output = {}
        for file in rename_files:
            file_name = file.split(".")[0]
            rename_file = file.replace(file_name, rename_map[file_name])
            os.rename(
                os.path.join(folder_path, file), os.path.join(folder_path, rename_file)
            )
            output[file] = rename_file

        return output

    def copy_rename_and_paste(
        self,
        src_folder: str,
        dst_folder: str,
        rename_map: dict[str, str]
    ) -> list[str]:

        '''
        Copies files from the source folder and renames them in the destination folder.
        Unlike the :meth:`GeoAnalyze.File.transfer_by_name` method, the source and destination
        folders can be the same, allowing for files to be renamed in place.

        Parameters
        ----------
        src_folder : str
            Path of the source folder containing the files to copy.

        dst_folder : str
            Path of the destination folder where the copied files will be placed with new names.

        rename_map : dict
            Dictionary where the keys are the original file names (without extensions)
            from the source folder, and the values are the new names (without extensions)
            for the destination folder. The file extensions will be preserved.

        Returns
        -------
        list
            A list of file names that were copied and renamed in the destination folder.
        '''

        src_contents = map(
            lambda x: os.path.join(src_folder, x), os.listdir(src_folder)
        )

        src_paths = filter(
            lambda x: os.path.isfile(x), src_contents
        )

        copy_paths = filter(
            lambda x: os.path.split(x)[-1].split('.')[0] in rename_map, src_paths
        )

        paste_files = []
        for path in copy_paths:
            copy_file = os.path.split(path)[-1]
            copy_name = copy_file.split('.')[0]
            paste_file = copy_file.replace(copy_name, rename_map[copy_name])
            shutil.copy2(
                os.path.join(src_folder, copy_file), os.path.join(dst_folder, paste_file)
            )
            paste_files.append(paste_file)

        return paste_files

    def extract_specific_extension(
        self,
        folder_path: str,
        extension: str
    ) -> list[str]:

        '''
        Extracts files with a specified extension from a folder.

        Parameters
        ----------
        folder_path : str
            Path of the input folder for searching files.

        extension : str
            File extension to search for, including the leading period (e.g., '.tif').

        Returns
        -------
        list
            A list of file names with the specified extension. Files with multiple
            extensions (e.g., '.tif.aux.xml') are excluded.
        '''

        folder_contents = map(
            lambda x: os.path.join(folder_path, x), os.listdir(folder_path)
        )

        file_paths = filter(
            lambda x: os.path.isfile(x), folder_contents
        )

        extension_paths = filter(
            lambda x: extension in x, file_paths
        )

        extension_files = map(
            lambda x: os.path.split(x)[-1], extension_paths
        )

        output = list(
            filter(
                lambda x: len(x.split('.')) == 2, extension_files
            )
        )

        return output
