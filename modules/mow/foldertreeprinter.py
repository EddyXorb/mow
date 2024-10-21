from pathlib import Path
from rich.tree import Tree
from rich.text import Text
from rich import print
from rich.filesize import decimal
from rich.markup import escape


class FolderTreePrinter:
    """
    Prints directory trees of a folder.
    """

    def print_tree_of(
        self,
        folder: Path,
        description: str = "",
        max_files: int = 300,
        max_same_filetype_per_folder=30,
    ):
        """
        Prints the directory tree of the specified folder.

        Parameters
        ----------
        folder : Path
            The root folder from which to print the directory tree.
        description : str, optional
            A description to be included in the tree output (default is an empty string).
        max_files : int, optional
            The maximum number of files to include in the tree (default is 300).
        max_same_filetype_per_folder : int, optional
            The maximum number of files of the same type to include per folder (default is 30).

        Returns
        -------
        None


        """
        tree = self._walk_directory(
            folder, Tree(description), max_same_filetype_per_folder=1, max_files=300
        )
        print(tree)

    def _walk_directory(
        self,
        directory: Path,
        tree: Tree,
        max_files: int = 9999,
        max_same_filetype_per_folder=30,
        iterations: list[int] = [0],
    ) -> Tree:
        """
        Recursively build a Tree with directory contents.

        Parameters
        ----------
        directory : Path
            The directory path to walk through.
        tree : Tree
            The Tree object to populate with directory contents.
        max_files : int, optional
            The maximum number of files to include in the tree (default is 9999).
        max_same_filetype_per_folder : int, optional
            The maximum number of files of the same type to include per folder (default is 30).
        iterations : list of int, optional
            A list containing a single integer to keep track of the number of iterations (default is [0]).

        Returns
        -------
        Tree
            The populated Tree object with the directory contents.

        """
        paths = sorted(
            Path(directory).iterdir(),
            key=lambda path: (path.is_file(), path.name.lower()),
        )

        files_treated_count = 0
        files_count = 0
        filetypes = set()

        for single_path in paths:
            # Remove hidden files
            if single_path.name.startswith("."):
                continue
            if single_path.is_dir():
                style = "dim" if single_path.name.startswith("__") else ""
                branch = tree.add(
                    f"[bold magenta]:open_file_folder: [link file://{single_path}]{escape(single_path.name)}",
                    style=style,
                    guide_style=style,
                )
                self._walk_directory(
                    single_path,
                    branch,
                    max_same_filetype_per_folder=max_same_filetype_per_folder,
                    max_files=max_files,
                    iterations=iterations,
                )
            else:  # is file
                files_count += 1
                filetype = single_path.suffix

                if (
                    files_treated_count >= max_same_filetype_per_folder
                    and filetype in filetypes
                ):  # assure that every filetype is shown at least once
                    continue

                if iterations[0] >= max_files:
                    continue

                files_treated_count += 1
                iterations[0] += 1
                filetypes.add(filetype)

                text_filename = Text(single_path.name, "green")
                text_filename.highlight_regex(r"\..*$", "bold red")
                text_filename.stylize(f"link file://{single_path}")
                file_size = single_path.stat().st_size
                text_filename.append(f" ({decimal(file_size)})", "blue")
                icon = "🐍 " if single_path.suffix == ".py" else "📄 "
                tree.add(Text(icon) + text_filename)

        if files_treated_count > max_same_filetype_per_folder:
            tree.add(f"... and {files_count - files_treated_count} more files")

        return tree
