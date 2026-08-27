"""RF source registry.

This module contains identity data only.  It deliberately contains no URL
normalisation, validation, scraping, or download logic.

Identity rules agreed for RF:

* A source is not necessarily a website.  It may be a website or one of its
  independently managed sections, a person, organisation, publication,
  platform account/channel, or an RF-original source.
* ``source_code`` is the stable RF identity.  It must not be derived from a
  URL, display name, adapter name, platform username, ISBN, or IMDb ID.
* One real website or platform may contain several independent RF sources.
* URLs are optional because some sources do not have their own website.
* ``external_id`` is optional and is intended for stable identities on shared
  platforms, for example a YouTube channel ID, Instagram account ID, ISBN, or
  IMDb ID.
* ``adapters`` names scraper/import adapters; adapter code and downloaded data
  live outside this registry.
* Do not assign codes to future people, publications, platform accounts, or
  RF-original sources until they are actually approved for the registry.

The current RF resource-code design reserves six characters for the source
namespace.  The original assigned source numbers 001-021 are therefore stored
as 000001-000021 without changing their identity.

Entry shape::

    {
        "origin_type": "external" | "rf",
        "platform": "web" | "youtube" | "instagram" | "amazon" | "imdb" | ...,
        "source_type": "website" | "website_section" | "person" |
                       "organisation" | "publication" | "channel" |
                       "account" | "rf_original",
        "external_id": str | None,
        "adapters": list[str],
        "urls": {
            "canonical": str | None,
            "current_prefixes": list[str],
            "aliases": list[str],
        },
        "display_name": str,
        "display_name_aliases": list[str],
    }
"""


SOURCE_CODE_WIDTH = 6


SOURCE_REGISTRY = {
    "000001": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["fluentize"],
        "urls": {
            "canonical": "https://fluentize.com",
            "current_prefixes": ["https://fluentize.com"],
            "aliases": [],
        },
        "display_name": "fluentize",
        "display_name_aliases": ["Fluentize"],
    },
    "000002": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["eslbrains"],
        "urls": {
            "canonical": "https://eslbrains.com",
            "current_prefixes": ["https://eslbrains.com"],
            "aliases": [],
        },
        "display_name": "eslbrains",
        "display_name_aliases": ["ESL Brains"],
    },
    "000003": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["english4tutors"],
        "urls": {
            "canonical": "https://english4tutors.com",
            "current_prefixes": ["https://english4tutors.com"],
            "aliases": [],
        },
        "display_name": "english4tutors",
        "display_name_aliases": ["english4Tutors", "English4Tutors"],
    },
    "000004": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["eslpals"],
        "urls": {
            "canonical": "https://eslpals.com",
            "current_prefixes": ["https://eslpals.com"],
            "aliases": [],
        },
        "display_name": "eslpals",
        "display_name_aliases": ["ESL Pals"],
    },
    "000005": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["onestopenglish"],
        "urls": {
            "canonical": "https://www.onestopenglish.com",
            "current_prefixes": ["https://www.onestopenglish.com"],
            "aliases": ["https://onestopenglish.com"],
        },
        "display_name": "onestopenglish",
        "display_name_aliases": ["Onestopenglish", "OneStopEnglish"],
    },
    "000006": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["yourenglishpal"],
        "urls": {
            "canonical": "https://yourenglishpal.com",
            "current_prefixes": ["https://yourenglishpal.com"],
            "aliases": [],
        },
        "display_name": "yourenglishpal",
        "display_name_aliases": ["Your English Pal"],
    },
    "000007": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["linguahouse"],
        "urls": {
            "canonical": "https://www.linguahouse.com",
            "current_prefixes": ["https://www.linguahouse.com"],
            "aliases": ["https://linguahouse.com"],
        },
        "display_name": "linguahouse",
        "display_name_aliases": ["Linguahouse"],
    },
    "000008": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["ellii"],
        "urls": {
            "canonical": "https://ellii.com",
            "current_prefixes": ["https://ellii.com"],
            "aliases": ["https://esllibrary.com", "https://www.esllibrary.com"],
        },
        "display_name": "ellii",
        "display_name_aliases": ["Ellii", "ESL Library"],
    },
    "000009": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["busyteacher"],
        "urls": {
            "canonical": "https://busyteacher.org",
            "current_prefixes": ["https://busyteacher.org"],
            "aliases": [],
        },
        "display_name": "busyteacher",
        "display_name_aliases": ["BusyTeacher"],
    },
    "000010": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["amerilingua"],
        "urls": {
            "canonical": "https://amerilingua.com",
            "current_prefixes": ["https://amerilingua.com"],
            "aliases": [],
        },
        "display_name": "amerilingua",
        "display_name_aliases": ["AmeriLingua"],
    },
    "000011": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["enghub"],
        "urls": {
            "canonical": "https://enghub.pro",
            "current_prefixes": ["https://enghub.pro"],
            "aliases": [],
        },
        "display_name": "enghub",
        "display_name_aliases": ["EngHub"],
    },
    "000012": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["espressoenglish"],
        "urls": {
            "canonical": "https://www.espressoenglish.net",
            "current_prefixes": ["https://www.espressoenglish.net"],
            "aliases": ["https://espressoenglish.net"],
        },
        "display_name": "espressoenglish",
        "display_name_aliases": ["Espresso English"],
    },
    "000013": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["eslkidstuff"],
        "urls": {
            "canonical": "https://www.eslkidstuff.com",
            "current_prefixes": ["https://www.eslkidstuff.com"],
            "aliases": ["https://eslkidstuff.com"],
        },
        "display_name": "eslkidstuff",
        "display_name_aliases": ["ESL KidStuff"],
    },
    "000014": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website_section",
        "external_id": None,
        "adapters": ["eslteenstuff"],
        "urls": {
            "canonical": "https://www.eslkidstuff.com/esl-teenstuff",
            "current_prefixes": [
                "https://www.eslkidstuff.com/esl-teenstuff",
                "https://www.eslkidstuff.com/teens",
            ],
            "aliases": [
                "https://eslteenstuff.com",
                "https://www.eslteenstuff.com",
            ],
        },
        "display_name": "eslteenstuff",
        "display_name_aliases": ["ESL TeenStuff", "teens"],
    },
    "000015": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["teach-this"],
        "urls": {
            "canonical": "https://www.teach-this.com",
            "current_prefixes": ["https://www.teach-this.com"],
            "aliases": ["https://teach-this.com"],
        },
        "display_name": "teach-this",
        "display_name_aliases": ["Teach-This", "Teach This"],
    },
    "000016": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["englishwsheets"],
        "urls": {
            "canonical": "https://www.englishwsheets.com",
            "current_prefixes": ["https://www.englishwsheets.com"],
            "aliases": ["https://englishwsheets.com"],
        },
        "display_name": "englishwsheets",
        "display_name_aliases": ["English Worksheets", "Englishwsheets"],
    },
    "000017": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["businessenglishpod"],
        "urls": {
            "canonical": "https://www.businessenglishpod.com",
            "current_prefixes": ["https://www.businessenglishpod.com"],
            "aliases": ["https://businessenglishpod.com"],
        },
        "display_name": "businessenglishpod",
        "display_name_aliases": ["Business English Pod", "business englishpod"],
    },
    "000018": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["printyjoy"],
        "urls": {
            "canonical": "https://printyjoy.com",
            "current_prefixes": ["https://printyjoy.com"],
            "aliases": [],
        },
        "display_name": "printyjoy",
        "display_name_aliases": ["PrintyJoy"],
    },
    "000019": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["thekidshouldseethis"],
        "urls": {
            "canonical": "https://thekidshouldseethis.com",
            "current_prefixes": ["https://thekidshouldseethis.com"],
            "aliases": [],
        },
        "display_name": "thekidshouldseethis",
        "display_name_aliases": ["The Kid Should See This"],
    },
    "000020": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["twinkl"],
        "urls": {
            "canonical": "https://www.twinkl.com",
            "current_prefixes": ["https://www.twinkl.com"],
            "aliases": ["https://twinkl.com"],
        },
        "display_name": "twinkl",
        "display_name_aliases": ["Twinkl"],
    },
    "000021": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["worksheetfun"],
        "urls": {
            "canonical": "https://www.worksheetfun.com",
            "current_prefixes": ["https://www.worksheetfun.com"],
            "aliases": ["https://worksheetfun.com"],
        },
        "display_name": "worksheetfun",
        "display_name_aliases": ["WorksheetFun", "worksheetfun.com"],
    },
    "000022": {
        "origin_type": "external",
        "platform": "web",
        "source_type": "website",
        "external_id": None,
        "adapters": ["esldiscussions"],
        "urls": {
            "canonical": "https://esldiscussions.com",
            "current_prefixes": ["https://esldiscussions.com"],
            "aliases": [],
        },
        "display_name": "esldiscussions",
        "display_name_aliases": ["ESL Discussions"],
    },
}