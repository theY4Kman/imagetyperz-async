import enum

__all__ = ['reCAPTCHAType']


class reCAPTCHAType(enum.IntEnum):

    ###
    # Determine the reCAPTCHA type automatically
    #
    #   NOTE: this is a guess as to what 0 means. it is the default in the
    #         official client, but values of 0 are not mentioned in the API docs.
    #
    AUTO = 0

    ###
    # Regular, visible-on-page-load reCAPTCHA v2
    #
    NORMAL = 1

    ###
    # Initially-invisible-until-form-submission reCAPTCHA v2
    #
    INVISIBLE = 2

    ###
    # Score-based reCAPTCHA v3
    #
    V3 = 3

    def __str__(self):
        # This ensures enum values are serialized as their integer values over
        # the wire in POST bodies, rather than their name (e.g. "reCAPTCHAType.NORMAL")
        return str(self.value)
