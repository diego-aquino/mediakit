def limit_text_length(text, limit_of_caracters):
    if len(text) > limit_of_caracters:
        partial_text_with_ellipsis = f'{text[:limit_of_caracters - 3]}...'

        return partial_text_with_ellipsis

    return text
