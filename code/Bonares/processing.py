# We need to have a recursive function to obtain all the relevant keys from the metadata
def print_dict_tree(d, indent=0):
    """
    Recursively print all keys in a dictionary as a tree structure.

    Parameters:
    d (dict): The dictionary to print.
    indent (int): Current indentation level (used for recursive depth).
    """
    # Iterate through all keys in the dictionary
    for key, value in d.items():
        # Print the key with indentation to show nesting
        print(" " * indent + str(key))

        # If the value is a dictionary, recurse into it with increased indentation
        if isinstance(value, dict):
            print_dict_tree(value, indent + 4)

def get_articles_with_absracts(list_of_articles):
    """
    Function to filter articles that have an abstract in their description metadata.

    Args:
    list_of_articles (list): A list of article data, where each article is expected to be a dictionary
                             containing metadata with resource descriptions.

    Returns:
    list: A new list containing only those articles that include an abstract in their metadata.
    """
    newlist = []
    for i in opnenagrardata[1:]:
        description = i['metadata']['resource']['descriptions']['description']
        if isinstance(description, list):
            for desc in description:
                if desc['@descriptionType'] == 'Abstract':
                    newlist.append(i)
        else:
            if description['@descriptionType'] == 'Abstract':
                newlist.append(i)
    return newlist