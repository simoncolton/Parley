from ParleyV2.Artefacts.Artefacts import *


class MarginUtils:

    def add_margin_comment(bar, text, comment_type):
        for c in bar.margin_comments:
            if c.comment_text == text and c.comment_type == comment_type:
                return
        bar.margin_comments.append(MarginComment(text, comment_type))

    def append_margin_comment_to_existing(bar, text, comment_type):
        for c in bar.margin_comments:
            if c.comment_text == text and c.comment_type == comment_type:
                return
            if c.comment_type == comment_type:
                c.comment_text = f"{c.comment_text} & {text}"
                return
        bar.margin_comments.append(MarginComment(text, comment_type))

    def has_comment(bar, text):
        for c in bar.margin_comments:
            if c.comment_text == text:
                return True
        return False

    def remove_comment(bar, text):
        bar.margin_comments = [c for c in bar.margin_comments if c.comment_text != text]
