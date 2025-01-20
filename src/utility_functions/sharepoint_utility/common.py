import os

def get_documents_library(ctx, library_title="Documents"):
    """
    Locate a document library by title, ensuring it's BaseTemplate 101 (document library).
    Returns the library list object if found, otherwise None.
    """
    web = ctx.web
    ctx.load(web)
    ctx.execute_query()

    lists = web.lists
    ctx.load(lists)
    ctx.execute_query()

    for sp_list in lists:
        if (
            sp_list.properties.get("Title") == library_title
            and sp_list.properties.get("BaseTemplate") == 101  # Document library
        ):
            return sp_list
    return None


def get_folder_by_server_relative_url(ctx, server_relative_url):
    """
    Given a full server-relative URL, returns the folder object.
    e.g. "/sites/MySite/Shared Documents/General"
    """
    folder = ctx.web.get_folder_by_server_relative_url(server_relative_url)
    ctx.load(folder)
    ctx.execute_query()
    return folder


def get_subfolder_by_name(parent_folder, ctx, subfolder_name):
    """
    Given a folder object, finds a subfolder by name. Returns the subfolder or None.
    """
    subfolders = parent_folder.folders
    ctx.load(subfolders)
    ctx.execute_query()

    for sf in subfolders:
        if sf.properties.get("Name") == subfolder_name:
            return sf
    return None