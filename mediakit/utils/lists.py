def flatten_list(list_to_flat: list, depth: int = 1):
    partially_flatten_list = [item for item in list_to_flat]

    for _ in range(depth):
        new_partially_flatten_list = []
        for items in partially_flatten_list:
            if type(items) is list:
                new_partially_flatten_list.extend(items)
            else:
                new_partially_flatten_list.append(items)

        partially_flatten_list = new_partially_flatten_list

    flatten_list = partially_flatten_list
    return flatten_list
