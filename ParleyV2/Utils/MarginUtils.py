from Artefacts.Artefacts import *


class MarginUtils:

    def add_margin_comment(bar, text, colour):
        for c in bar.margin_comments:
            if c.comment_text == text and c.comment_colour == colour:
                return
        bar.margin_comments.append(MarginComment(text, colour))

    def has_comment(bar, text):
        for c in bar.margin_comments:
            if c.comment_text == text:
                return True
        return False

    def remove_comment(bar, text):
        bar.margin_comments = [c for c in bar.margin_comments if c.comment_text != text]
