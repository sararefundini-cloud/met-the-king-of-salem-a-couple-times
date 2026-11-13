"""KJV motif lexicon for Sara's Bible Stories Bingo + Stones.

Each row: motif, subgroup, term, match_type, confidence, notes, report_as
match_type:
  exact   - case-insensitive whole-word match (after text normalization)
  phrase  - case-insensitive multi-word phrase with word boundaries
  regex   - searched against the normalized verse text (IGNORECASE)
  special - handled in build_graph.py (see handler in notes / report_as)
confidence: high, medium, low
"""

# Motifs in bingo-board order, Stones last.
MOTIF_ORDER = [
    "Donkey",
    "Precious Metals",
    "Sheep",
    "Blood",
    "Wine & Grapes",
    "Sword",
    "Grapes",
    "Bread",
    "Parting Water",
    "Repeating Names",
    "Colors",
    "Brides",
    "Providence",
    "Light",
    "Fire",
    "Natural Disasters",
    "Animals",
    "Giants",
    "Egypt",
    "Death in General",
    "Infant Death",
    "Name Meaning",
    "Apparel",
    "Tree",
    "Death as a Consequence",
    "Stones",
    "I AM",
    "Alchemist overlap",
]


def R(motif, term, match_type="exact", subgroup="", confidence="high", notes="", report_as=""):
    return {
        "motif": motif,
        "subgroup": subgroup,
        "term": term,
        "match_type": match_type,
        "confidence": confidence,
        "notes": notes,
        "report_as": report_as or term,
    }


def exact_words(motif, words, subgroup="", confidence="high", notes=""):
    return [R(motif, w, "exact", subgroup, confidence, notes) for w in words]


def phrases(motif, items, subgroup="", confidence="high", notes=""):
    return [R(motif, p, "phrase", subgroup, confidence, notes) for p in items]


def build_lexicon():
    rows = []

    # ---------- Donkey ----------
    rows += exact_words("Donkey", [
        "ass", "asses", "mule", "mules",
    ])
    rows += exact_words("Donkey", ["colt", "colts", "foal", "foals"], confidence="medium",
                       notes="Colt/foal can be of an ass, horse, or camel; often an ass in narrative (e.g. Triumphal Entry).")
    rows += phrases("Donkey", ["she ass", "she asses", "he ass", "he asses", "wild ass", "wild asses"])

    # ---------- Precious Metals ----------
    rows += exact_words("Precious Metals", [
        "gold", "golden", "goldsmith", "goldsmiths",
        "silver", "silversmith", "silversmiths",
    ])
    # brass/iron omitted: not precious

    # ---------- Sheep ----------
    rows += exact_words("Sheep", [
        "sheep", "sheepfold", "sheepfolds", "sheepcote", "sheepcotes",
        "lamb", "lambs",
        "ewe", "ewes", "ewelamb", "ewelambs",
        "rams",  # safer than 'ram' alone
        "shepherd", "shepherds",
    ])
    rows += exact_words("Sheep", ["ram"], confidence="medium",
                       notes="Also the personal name Ram in genealogies (Ruth, Chronicles).")
    rows += exact_words("Sheep", ["flock", "flocks"], confidence="medium",
                       notes="Flock can include goats or mixed herds.")
    rows += exact_words("Sheep", ["wool", "woollen", "woolen"], confidence="medium",
                       notes="Material, not always a living sheep in the verse.")

    # ---------- Blood ----------
    rows += exact_words("Blood", [
        "blood", "bloods", "bloody", "bloodshed", "bloodthirsty",
        "bleed", "bled", "bleeding", "bleedeth",
    ])

    # ---------- Wine & Grapes (superset: drink + fruit + vine) ----------
    rows += exact_words("Wine & Grapes", [
        "wine", "wines", "winepress", "winepresses", "winefat", "winefats",
        "winebibber", "winebibbers",
        "vinegar",
        "flagon", "flagons",
        "grape", "grapes", "grapegatherer", "grapegatherers",
        "vintage",
        "vine", "vines", "vineyard", "vineyards", "vinegrower",
        "raisin", "raisins",
    ])
    rows += phrases("Wine & Grapes", ["strong drink", "blood of grapes", "blood of the grape"])

    # ---------- Sword ----------
    rows += exact_words("Sword", ["sword", "swords", "twoedged", "twoedged"])
    rows += phrases("Sword", ["two edged", "two edged sword", "edge of the sword"])

    # ---------- Grapes (fruit / cluster / vine focus; overlaps Wine & Grapes) ----------
    rows += exact_words("Grapes", [
        "grape", "grapes", "grapegatherer", "grapegatherers",
        "vintage",
        "vine", "vines", "vineyard", "vineyards",
        "raisin", "raisins",
    ])
    rows += exact_words("Grapes", ["cluster", "clusters"], confidence="medium",
                       notes="Usually grapes or fruit in KJV, but not always specified.")
    rows += phrases("Grapes", ["blood of grapes", "blood of the grape"])

    # ---------- Bread ----------
    rows += exact_words("Bread", [
        "bread", "shewbread",
        "loaf", "loaves",
        "wafer", "wafers",
        "unleavened",
    ])
    rows += exact_words("Bread", ["manna"], confidence="medium",
                       notes="Treated as 'bread from heaven', not baked bread.")
    rows += exact_words("Bread", ["leaven", "leavened", "leaveneth"], confidence="medium",
                       notes="Bread-related, including metaphorical leaven.")
    rows += exact_words("Bread", ["cake", "cakes"], confidence="low",
                       notes="May be cakes of bread, or cakes of figs/raisins.")
    rows += exact_words("Bread", ["crumb", "crumbs"], confidence="medium")

    # ---------- Parting Water ----------
    rows += phrases("Parting Water", [
        "divided the waters",
        "waters were divided",
        "divided the sea",
        "divided the red sea",
        "parted hither",
        "parted hither and thither",
        "waters were a wall",
        "midst of the sea upon the dry",
        "through the sea on dry",
        "went into the midst of the sea",
        "passed through the sea",
        "passed through the red sea",
        "walked upon dry land in the midst of the sea",
        "dry ground in the midst of the sea",
        "made the sea dry",
        "the sea reserved",  # won't match; placeholder avoided
        "rose up upon an heap",
        "stood and rose up upon an heap",
        "waters of jordan",
        "waters which came down from above stood",
        "dried up the waters",
        "dried up the sea",
        "dried the sea",
        "smote the waters",
        "rod over the sea",
        "lift thou up thy rod",
        "red sea",
    ], confidence="high", notes="Includes commemorative 'Red sea' references as well as the event verses. Loose 'water near dry land/cut off' patterns were dropped to avoid false hits (e.g. drought, geography, creation dry land). Genesis 1:7 still matches the phrase 'divided the waters'.")
    rows += phrases("Parting Water", [
        "waters of the jordan were cut off",
        "waters of jordan were cut off",
        "dried up the waters of jordan",
        "passed through the red sea",
        "through the red sea",
    ])

    # ---------- Repeating Names ----------
    rows.append(R(
        "Repeating Names",
        "consecutive_repeated_name",
        "special",
        confidence="high",
        notes="Vocative name doubled with a comma (Abraham, Abraham; Saul, Saul; Eli, Eli; Lord, Lord). Ignores genealogy and clause-boundary repeats (Noah: Noah; Phinehas, Phinehas begat). Excludes non-names (Awake, Peace, Alas, Aha) and function words.",
        report_as="consecutive repeated name",
    ))
    rows += phrases("Repeating Names", ["my son, my son", "my God, my God"], confidence="medium",
                    notes="Vocative repetitions used as name-like address (David for Absalom; 'My God, my God' in Ps 22 / the cross).")

    # ---------- Colors ----------
    color_words = [
        "scarlet", "purple", "blue", "crimson", "vermilion",
        "white", "black", "green", "yellow", "amber",
        "bay", "grisled", "grizzled", "speckled", "spotted", "brown",
        "grey", "gray", "hoary", "ruddy", "pale",
        "colour", "colour", "colours", "colored", "coloured", "color", "colors",
    ]
    rows += exact_words("Colors", color_words)
    rows += exact_words("Colors", ["red"], confidence="high",
                        notes="Occurrences inside the phrase 'Red sea' are excluded (place name, not a color mention).")
    rows += exact_words("Colors", ["hoar"], confidence="low",
                        notes="Often 'hoar frost' or 'hoar hairs' (gray), not always a pure color word.")

    # ---------- Brides ----------
    rows += exact_words("Brides", [
        "bride", "brides", "bridal",
        "bridegroom", "bridegrooms",
        "marriage", "marriages", "marry", "married", "marrieth", "marrying",
        "wedding",
        "betroth", "betrothed",
        "espouse", "espoused", "espousals",
        "spouse", "spouses",
    ])

    # ---------- Providence (free space; abstract; lower overall confidence) ----------
    rows += exact_words("Providence", ["providence"], confidence="medium",
                        notes="The only KJV use of the noun is Acts 24:2 (Tertullus flattering Felix), not divine providence.")
    rows += exact_words("Providence", [
        "provide", "provided", "provideth", "providing", "provider",
    ], confidence="medium", notes="Lexical 'provide' family; not all uses are theological providence.")
    rows += exact_words("Providence", ["provision", "provisions"], confidence="low",
                        notes="Usually food or military supply.")
    rows += exact_words("Providence", ["jehovahjireh"], confidence="high",
                        notes="Joined form of Jehovah–jireh, 'the LORD will provide'.")
    rows += phrases("Providence", [
        "will provide",
        "the lord will provide",
        "god will provide",
        "all things work together for good",
        "careth for you",
        "according to his purpose",
    ], confidence="high")
    rows += exact_words("Providence", ["predestinate", "predestinated"], confidence="medium",
                        notes="Related doctrine of divine purpose; not the everyday word providence.")

    # ---------- Light ----------
    rows += exact_words("Light", [
        "light", "lights", "lighted", "lighteth",
        "lighten", "lightened", "lighteneth",
        "enlighten", "enlightened", "enlighteneth", "enlightening",
        "candle", "candles", "candlestick", "candlesticks",
        "lamp", "lamps",
        "lantern", "lanterns",
        "shine", "shined", "shineth", "shining", "shone",
        "bright", "brightness", "brightly",
    ])
    rows += phrases("Light", ["day star"])
    # deliberately omitted: lighter, lightly, lightness, lightning(s)

    # ---------- Fire ----------
    rows += exact_words("Fire", [
        "fire", "fires", "fiery",
        "flame", "flames", "flaming",
        "burn", "burned", "burnt", "burning", "burneth", "burnest",
        "kindle", "kindled", "kindleth",
    ])
    rows += exact_words("Fire", ["coal", "coals"], confidence="medium",
                        notes="Often 'coals of fire', sometimes cooking or metalwork.")
    rows += exact_words("Fire", ["furnace", "furnaces"], confidence="medium",
                        notes="Smelting or judgment (fiery furnace).")
    rows += exact_words("Fire", ["brimstone"], confidence="medium",
                        notes="Shared with Natural Disasters.")

    # ---------- Natural Disasters ----------
    rows += exact_words("Natural Disasters", [
        "earthquake", "earthquakes",
        "flood", "floods", "flooded",
        "famine", "famines",
        "pestilence", "pestilences",
        "drought",
        "dearth",
        "hail", "hailstones",
        "tempest", "tempests",
        "storm", "storms", "stormy",
        "whirlwind", "whirlwinds",
        "thunder", "thunders", "thundered", "thundereth", "thunderings", "thunderbolts",
        "lightning", "lightnings",
        "plague", "plagues",
        "brimstone",
        "locust", "locusts",
        "mildew",
        "blasting",
    ])
    rows += exact_words("Natural Disasters", ["overflowed", "overflowing"], confidence="medium",
                        notes="Sometimes flood imagery, sometimes abundance.")

    # ---------- Animals (other than sheep/donkey families, which have their own motifs) ----------
    animals = [
        # livestock / herd (not sheep or ass)
        "cattle", "ox", "oxen", "bull", "bulls", "bullock", "bullocks",
        "cow", "cows", "kine", "heifer", "heifers", "calf", "calves",
        "goat", "goats", "kid", "kids",
        "horse", "horses",
        "camel", "camels", "dromedary", "dromedaries",
        # predators / wild
        "lion", "lions", "lioness", "lionesses", "lionlike",
        "bear", "bears",
        "wolf", "wolves",
        "leopard", "leopards",
        "dog", "dogs",
        "swine",
        "fox", "foxes",
        "hart", "harts", "hind", "hinds",
        "roe", "roes", "roebuck", "roebucks",
        "deer", "pygarg", "chamois",
        "coney", "conies", "hare", "hares",
        "mouse", "mice", "weasel", "ferret",
        "mole", "moles",
        "badger", "badgers",
        "bat", "bats",
        "ape", "apes",
        "unicorn", "unicorns",
        "behemoth", "leviathan",
        "greyhound",
        # reptiles / 'dragons'
        "serpent", "serpents", "viper", "vipers", "asp", "asps",
        "adder", "adders", "cockatrice", "cockatrices",
        "dragon", "dragons",
        "lizard", "lizards", "tortoise", "chameleon", "snail", "snails",
        "scorpion", "scorpions",
        # water
        "whale", "whales", "fish", "fishes",
        # birds
        "bird", "birds", "fowl", "fowls",
        "eagle", "eagles", "raven", "ravens",
        "dove", "doves", "pigeon", "pigeons",
        "sparrow", "sparrows",
        "owl", "owls",
        "stork", "heron", "herons", "pelican", "pelicans",
        "cormorant", "cormorants",
        "hawk", "hawks", "nighthawk",
        "vulture", "vultures", "ossifrage", "ospray", "osprey",
        "kite", "kites", "glede",
        "cuckow", "cuckoo",
        "lapwing", "bittern",
        "quail", "quails",
        "cock", "hen", "chicken", "chickens",
        "turtledove", "turtledoves",
        "peacock", "peacocks",
        "swan", "swans",
        # insects / creeping
        "locust", "locusts", "grasshopper", "grasshoppers",
        "palmerworm", "cankerworm", "caterpillar", "caterpillars", "caterpiller", "caterpillers",
        "bee", "bees", "flies",  # not bare 'fly' (verb)
        "worm", "worms", "moth", "moths",
        "hornet", "hornets",
        "spider", "spiders",
        "ant", "ants",
        "flea", "fleas",
        "lice", "louse",
        "frog", "frogs",
        "beetle", "beetles",
        "gnat", "gnats",
        "horseleach", "horseleech",
        # general
        "beast", "beasts",
    ]
    rows += exact_words("Animals", animals,
                        notes="Excludes sheep/ram/lamb/ewe/flock and ass/mule/colt (those have their own motifs).")
    rows += phrases("Animals", [
        "fallow deer",
        "great fish",
        "creeping thing",
        "creeping things",
        "night hawk",
        "herd of swine",
        "sea monster", "sea monsters",
        "turtle dove", "turtle doves",
    ])
    rows += exact_words("Animals", ["herd", "herds"], confidence="medium",
                        notes="Usually cattle, not always.")
    rows += exact_words("Animals", ["horseman", "horsemen"], confidence="low",
                        notes="Military cavalry more than the animal itself.")

    # ---------- Giants ----------
    rows += exact_words("Giants", [
        "giant", "giants",
        "anak", "anakim", "anakims",
        "rephaim", "rephaims",
        "emim", "emims",
        "zamzummim", "zamzummims", "zuzim", "zuzims",
        "og",
        "goliath",
        "lahmi",
        "ishbibenob",
        "saph",
    ])
    rows += phrases("Giants", [
        "sons of anak",
        "children of anak",
        "sons of the giant",
        "children of the giant",
        "brother of goliath",
        "valley of rephaim",
        "valley of the giants",
        "men of great stature",
        "of great stature",
        "six fingers",
        "six toes",
        "og king of bashan",
    ], confidence="high")
    rows += exact_words("Giants", ["arba"], confidence="low",
                        notes="Father of Anak, but also embedded in the place name Kirjath-arba / Kirjatharba.")

    # ---------- Egypt ----------
    rows += exact_words("Egypt", [
        "egypt", "egyptian", "egyptians",
        "pharaoh", "pharaohs",
        "pharaohnecho", "pharaohnechoh", "pharaohhophra",
        "mizraim",
        "zoan", "noph", "pathros",
        "rameses", "raamses", "pithom",
    ])
    rows += exact_words("Egypt", ["goshen"], confidence="medium",
                        notes="The land of Goshen in Egypt; not every later echo is clearly Egyptian context.")
    rows += phrases("Egypt", ["land of ham"], confidence="medium",
                    notes="Poetic name for Egypt in some psalms and prophets.")

    # ---------- Death in General ----------
    rows += exact_words("Death in General", [
        "death", "deaths",
        "die", "died", "diest", "dieth", "dying",
        "dead", "deadly", "deadness",
        "slay", "slayeth", "slaying", "slain", "slew", "slayer", "slayers",
        "kill", "killed", "killeth", "killing",
        "grave", "graves",
        "sepulchre", "sepulchres",
        "bury", "buried", "burieth", "burying", "burial", "buriers", "buryingplace",
        "carcase", "carcases",
        "mortal", "mortality",
    ])
    rows += exact_words("Death in General", ["perish", "perished", "perisheth", "perishing"], confidence="medium",
                        notes="Can mean ruin or loss, not only physical death.")
    rows += phrases("Death in General", [
        "gave up the ghost",
        "give up the ghost",
        "given up the ghost",
        "yielded up the ghost",
        "slept with his fathers",
        "slept with their fathers",
        "sleep with thy fathers",
        "slept with his fathers",
    ])

    # ---------- Infant Death ----------
    rows.append(R(
        "Infant Death",
        r"\binfants?\b",
        "regex",
        confidence="medium",
        notes="The word infant/infants only when the verse also has a death/violence verb. Drops blessing scenes such as Luke 18:15, and Isaiah 65:20 (an infant of days in a longevity blessing, not a child dying).",
        report_as="infant(s) in a death/violence context",
    ))
    rows.append(R(
        "Infant Death",
        r"\bsucklings?\b",
        "regex",
        confidence="medium",
        notes="Included when the verse also has a death/violence verb (die, slay, dash, kill, smote, dead, death, perish, destroy).",
        report_as="suckling(s) in a death/violence context",
    ))
    rows += phrases("Infant Death", [
        "child died",
        "child is dead",
        "child was dead",
        "the child is dead",
        "the child died",
        "two years old and under",
        "slew all the children",
        "slew all the male children",
        "if it be a son, then ye shall kill him",
        "every son that is born ye shall cast into the river",
    ], notes="The last two phrases are Pharaoh's order to kill Hebrew baby boys (Exodus 1:16, 1:22).")
    rows.append(R(
        "Infant Death",
        r"\blittle ones\b",
        "regex",
        confidence="medium",
        notes="Only when the verse also has dash/dashed/slay/slew/slain/kill/die/dead/death/perish/destroy, and the little ones themselves are being killed or destroyed. Drops Matthew 18:14 (it is not the Father's will that little ones perish) and Zechariah 13:7 (the shepherd's flock, not children dying).",
        report_as="little ones in a death/violence context",
    ))
    rows.append(R(
        "Infant Death",
        r"\byoung child(?:ren)?\b",
        "regex",
        confidence="medium",
        notes="Only when the verse also has a death/violence verb (catches Herod's massacre and similar).",
        report_as="young child(ren) in a death/violence context",
    ))
    rows.append(R(
        "Infant Death",
        r"\bfirstborn\b",
        "regex",
        confidence="medium",
        notes="Only when the verse also has a death/violence verb. Excludes theological 'firstborn from the dead' / 'firstborn of every creature' / 'church of the firstborn'; adult firstborn genealogies (Er in Genesis 38:7 and 1 Chronicles 2:3); and verses that consecrate Israel's firstborn (Numbers 3:13, 8:17) even when they recall the Egyptian plague.",
        report_as="firstborn in a death context",
    ))
    rows.append(R(
        "Infant Death",
        r"\bdashed?(?:\s+in\s+pieces)?\b.{0,40}\b(little ones|infants?|sucklings?|children|child)\b|\b(little ones|infants?|sucklings?|children)\b.{0,40}\bdashed?(?:\s+in\s+pieces)?\b",
        "regex",
        confidence="high",
        notes="Dashing of little ones / children / infants.",
        report_as="dashed little ones/children",
    ))

    # ---------- Name Meaning ----------
    rows += phrases("Name Meaning", [
        "being interpreted",
        "which being interpreted",
        "which is, being interpreted",
        "that is, being interpreted",
        "by interpretation",
        "which is by interpretation",
        "is by interpretation",
        "called his name",
        "called her name",
        "called their name",
        "called the name",
        "called the name of",
        "shall call his name",
        "shalt call his name",
        "thou shalt call his name",
        "his name was called",
        "her name was called",
        "the name of it was called",
        "name of the place was called",
        "therefore the name of",
        "therefore was the name",
        "the name of it called",
        "called his wife's name",
        "called his son's name",
        "called her son's name",
        "called his daughter's name",
    ], confidence="high",
       notes="Standard KJV naming and etymology formulae. Does not catch every folk etymology that lacks these frames (e.g. Cain in Gen 4:1, which has no 'called his name' clause).")
    rows += phrases("Name Meaning", ["that is to say"], confidence="low",
                    notes="Sometimes a name gloss, sometimes a general clarification.")

    # ---------- Apparel ----------
    rows += exact_words("Apparel", [
        "apparel", "apparelled", "appareled",
        "garment", "garments",
        "raiment",
        "robe", "robes",
        "coat", "coats",
        "vesture",
        "clothe", "clothed", "clothes", "clothing", "clothest", "clotheth",
        "cloth", "cloths",
        "sackcloth",
        "veil", "veils", "vail", "vails",
        "mitre", "mitres",
        "ephod",
        "breeches",
        "girdle", "girdles",
        "shoe", "shoes", "shoelatchet",
        "bonnet", "bonnets",
        "cloke", "cloak",
        "mantle", "mantles",
        "skirt", "skirts",
        "napkin", "napkins",
        "handkerchief", "handkerchiefs",
        "attire", "attired",
        "swaddling",
    ])
    rows += exact_words("Apparel", ["linen"], confidence="medium",
                        notes="Often clothing (fine linen), sometimes tabernacle material.")
    rows += exact_words("Apparel", ["woollen", "woolen"], confidence="medium")
    rows += exact_words("Apparel", ["gird", "girded", "girdeth"], confidence="medium",
                        notes="Includes 'gird up thy loins' (prepare), not only putting on a girdle.")
    rows += phrases("Apparel", [
        "arrayed in",
        "arrayed with",
        "fine linen",
        "swaddling clothes",
    ])

    # ---------- Tree ----------
    rows += exact_words("Tree", [
        "tree", "trees",
        "oak", "oaks",
        "cedar", "cedars",
        "fir", "firs",
        "pine", "pines",
        "olive", "olives", "oliveyard", "oliveyards",
        "gopher",
        "shittim",
        "willow", "willows",
        "poplar", "poplars",
        "myrtle", "myrtles",
        "juniper",
        "chestnut", "chestnuts",
        "cypress",
        "algum", "algums", "almug", "almugs",
        "sycamine", "sycomore", "sycomores", "sycamore", "sycamores",
        "mulberry", "mulberries",
        "grove", "groves",
        "forest", "forests",
        "bush", "bushes",
        "bough", "boughs",
    ])
    rows += exact_words("Tree", ["fig", "figs"], confidence="medium",
                        notes="Includes the fruit as well as the fig tree.")
    rows += exact_words("Tree", ["almond", "almonds"], confidence="medium",
                        notes="Tree or nuts (Aaron's rod, food).")
    rows += exact_words("Tree", ["pomegranate", "pomegranates"], confidence="medium",
                        notes="Fruit, ornament, or tree.")
    rows += exact_words("Tree", ["branch", "branches"], confidence="medium",
                        notes="Often literal limbs; also messianic/tribal metaphor.")
    rows += phrases("Tree", [
        "palm tree", "palm trees",
        "teil tree",
        "box tree",
        "ash tree",
        "fig tree", "fig trees",
        "olive tree", "olive trees",
        "hanged on a tree",
        "hangeth on a tree",
        "hanging on a tree",
        "cedar wood",
        "shittim wood",
        "gopher wood",
    ])

    # ---------- Death as a Consequence (legal / judgment / penalty formulae) ----------
    rows += phrases("Death as a Consequence", [
        "surely die",
        "shalt surely die",
        "shall surely die",
        "ye shall surely die",
        "thou shalt surely die",
        "he shall surely die",
        "they shall surely die",
        "put to death",
        "be put to death",
        "shall be put to death",
        "surely be put to death",
        "wages of sin",
        "wages of sin is death",
        "soul that sinneth",
        "the soul that sinneth, it shall die",
        "blood shall be upon",
        "blood shall be upon them",
        "his blood be upon",
        "his blood shall be",
        "blood be upon",
        "cut off from among",
        "cut off from his people",
        "cut off from the people",
        "cut off from the congregation",
        "worthy of death",
        "guilty of death",
        "sin unto death",
        "die the death",
        "hanged on a tree",
        "hangeth on a tree",
        "stoned till he die",
        "stone him till",
        "until he die",
        "till he die",
        "till they die",
    ], confidence="high",
       notes="Legal and theological death-as-penalty / judgment formulae.")
    rows.append(R(
        "Death as a Consequence",
        r"\b(the lord|the lord god|god|the lord thy god)\s+smote\b|\bsmote him\b|\bsmote them\b",
        "regex",
        confidence="low",
        notes="Divine 'smote' often (not always) means death as judgment. Lower confidence; some smitings are illness or defeat.",
        report_as="divine/fatal smote",
    ))

    # ---------- Stones (reworked: God is the stone/rock) ----------
    # Subgroups: God as Rock/Stone; Law in stone; stoning; caves and rock
    # shelters; water from the rock. No gemstones.

    godrock = "God as Rock/Stone"
    rows += phrases("Stones", [
        "my rock",
        "our rock",
        "their rock",
        "the lord is my rock",
        "he is my rock",
        "thou art my rock",
        "he is the rock",
        "he only is my rock",
        "blessed be my rock",
        "god my rock",
        "god of my rock",
        "o lord my rock",
        "god was their rock",
        "rock of israel",
        "stone of israel",
        "rock of my salvation",
        "rock of our salvation",
        "rock of his salvation",
        "rock of my strength",
        "rock of my refuge",
        "the rock that begat thee",
        "who is a rock save our god",
        "who is a rock save the lord",
        "neither is there any rock",
        "chief corner stone",
        "head of the corner",
        "head stone of the corner",
        "precious corner stone",
        "tried stone",
        "stone which the builders refused",
        "stone which the builders rejected",
        "stone which the builders disallowed",
        "stone of stumbling",
        "stumbling stone",
        "stumblingstone",
        "rock of offence",
        "spiritual rock",
        "that rock was christ",
        "living stone",
        "lively stones",
        "upon this rock i will build",
        "stone was cut out",
        "cut out of the mountain without hands",
        "cut out without hands",
        "a stone cut out",
        "look unto the rock whence ye are hewn",
        "the rock whence ye are hewn",
        "i lay in zion for a foundation a stone",
    ], subgroup=godrock,
       notes="Titles and typological identifications of God/Christ as rock or stone. 'Upon this rock I will build' (Matt 16:18) is included as medium-confidence because the referent is debated. Bare 'the rock' (a boulder, Horeb, a cave) is not in this subgroup.")
    # Mark the debated one medium by a second pass? Keep a dedicated medium row:
    # already in the list; add a note on that one via a separate medium phrase already included.
    rows.append(R(
        "Stones",
        "upon this rock i will build",
        "phrase",
        subgroup=godrock,
        confidence="medium",
        notes="Matthew 16:18. Included because the verse names a rock on which the church is built; the exact referent (Christ, Peter's confession, Peter) is debated.",
        report_as="upon this rock I will build",
    ))

    law = "Law in stone"
    rows += phrases("Stones", [
        "tables of stone",
        "table of stone",
        "two tables of stone",
        "tables of testimony",
        "two tables of the testimony",
        "tables of the covenant",
        "two tables of the covenant",
        "written with the finger of god",
        "altar of stone",
        "altars of stone",
        "altar of whole stones",
        "pillar of stone",
        "pillars of stone",
        "stone for a pillar",
        "set it up for a pillar",
        "set up a pillar",
        "set up a stone",
        "set it up for a stone",
        "this stone, which i have set for a pillar",
        "ebenezer",
        "heap of stones",
        "twelve stones",
        "wrote upon the stones",
        "write upon them all the words",
        "took a great stone, and set it up",
        "set them a great stone",
        "two tables which moses",
    ], subgroup=law,
       notes="The law written in stone, stone altars, and memorial/pillar stones (Bethel pillar, Ebenezer, Jordan's twelve stones, Joshua's witness stone, Galeed heap). Not every mention of the city Bethel.")
    rows.append(R(
        "Stones",
        r"\btwo tables\b(?=.*\b(stone|covenant|testimony|moses|horeb|brake)\b)|\b(stone|covenant|testimony|moses|horeb|brake)\b.*\btwo tables\b",
        "regex",
        subgroup=law,
        confidence="high",
        notes="Catches 'the two tables' when the verse is clearly the Sinai tablets (not Ezekiel's temple offering tables).",
        report_as="two tables (Sinai)",
    ))

    st = "stoning"
    rows += exact_words("Stones", ["stoned", "stoneth", "stoning"], subgroup=st)
    rows += phrases("Stones", [
        "stone him",
        "stone her",
        "stone them",
        "stone thee",
        "stone me",
        "be stoned",
        "are stoned",
        "were stoned",
        "was stoned",
        "is stoned",
        "shall be stoned",
        "stone with stones",
        "stoned with stones",
        "stoned with",
        "let us stone",
        "sought to stone",
        "took up stones",
        "take up stones",
        "cast a stone",
        "first cast a stone",
    ], subgroup=st,
       notes="Judicial or mob stoning. David's sling stone is not included. When the same verse also has 'the Lord said/commanded', that is flagged in findings as an explicit divine order.")
    rows.append(R(
        "Stones",
        r"\b(the lord (said|spake|commanded).{0,120}\b(stone him|stone her|stone them|stone with stones|stoned)|((stone him|stone her|stone them|stone with stones|stoned).{0,120}\b(the lord (said|spake|commanded)|as the lord commanded)))",
        "regex",
        subgroup=st,
        confidence="high",
        notes="Same-verse pairing of a stoning act/command with 'the Lord said/spake/commanded'.",
        report_as="the LORD said/commanded ... stone",
    ))

    cave = "caves and rock shelters"
    rows += exact_words("Stones", ["cave", "caves"], subgroup=cave)
    rows += exact_words("Stones", ["machpelah", "adullam"], subgroup=cave)
    rows += phrases("Stones", [
        "clift of the rock",
        "cleft of the rock",
        "clefts of the rock",
        "clifts of the rocks",
        "hole of the rock",
        "holes of the rocks",
        "hewn out in the rock",
        "hewn out of a rock",
        "hewn in stone",
        "hewed thee out a sepulchre",
        "sepulchre on high",
        "rolled a great stone",
        "rolled a stone",
        "rolled back the stone",
        "rolled away the stone",
        "stone was rolled away",
        "stone rolled away",
        "stone taken away from the sepulchre",
        "roll us away the stone",
        "roll great stones upon the mouth of the cave",
        "entering in of the cave",
        "unto a cave, and lodged",
        "dens and caves",
        "dens and in the rocks",
        "den of lions",
        "mouth of the den",
        "out of the den",
        "into the den",
    ], subgroup=cave,
       notes="Caves, rock clefts, patriarchal tombs (Machpelah), David's Adullam, Elijah at Horeb, the tomb hewn in the rock and the rolled stone, Daniel's den, and dens used as human shelters. Animal dens and 'den of thieves/robbers' are not included unless a more specific shelter phrase also hits.")

    water = "water from the rock"
    rows += phrases("Stones", [
        "smote the rock",
        "smite the rock",
        "speak ye unto the rock",
        "speak unto the rock",
        "water out of the rock",
        "waters out of the rock",
        "water out of this rock",
        "water out of the rock of flint",
        "water out of the flinty rock",
        "brought streams also out of the rock",
        "clave the rock",
        "honey out of the rock",
        "oil out of the flinty rock",
        "rivers out of the rock",
        "drinking water out of the rock",
        "there shall come water out of it",
        "the same spiritual drink",
    ], subgroup=water)
    rows += exact_words("Stones", ["meribah", "massah"], subgroup=water, confidence="medium",
                       notes="Place-names of the water-from-the-rock episodes and later commemorations of them.")
    # 1 Cor 10:4 is both God-as-Rock and water-from-the-rock; spiritual rock phrase already in godrock.
    rows += phrases("Stones", [
        "they drank of that spiritual rock",
        "that rock was christ",
    ], subgroup=water, confidence="high",
       notes="Paul's reading of the wilderness water as the spiritual Rock, who is Christ. Also listed under God as Rock/Stone.")

    # ---------- I AM ----------
    joh = "Johannine I am"
    rows += phrases("I AM", [
        "i am the bread of life",
        "i am that bread of life",
        "i am the living bread",
        "i am the bread which came down from heaven",
    ], subgroup=joh, notes="The bread-of-life cluster in John 6, treated as one official 'I am' statement with its variant wordings.")
    # report variants under their own term strings so refs stay precise; findings group them.
    rows += phrases("I AM", [
        "i am the light of the world",
        "i am the door",
        "i am the door of the sheep",
        "i am the good shepherd",
        "i am the resurrection, and the life",
        "i am the way, the truth, and the life",
        "i am the true vine",
        "i am the vine",
        "before abraham was, i am",
    ], subgroup=joh)

    ot = "OT echo"
    rows += phrases("I AM", [
        "i am that i am",
        "i am hath sent me",
    ], subgroup=ot,
       notes="Exodus 3:14. The divine name formula that the Johannine 'Before Abraham was, I am' echoes. Linked from that Term via the ot_refs property, not a graph relationship.")
    rows += phrases("I AM", [
        "i am the lord",
        "i am the lord thy god",
        "i am the lord your god",
    ], subgroup=ot,
       notes="The recurring self-identification 'I am the LORD'. OT echo of the absolute 'I am' (John 8:58). All matched refs are stored on the Term and copied onto the Johannine Term's ot_refs property.")
    # typological echoes of the seven statements
    rows += phrases("I AM", [
        "manna",
        "bread from heaven",
        "bread which came down from heaven",
    ], subgroup=ot,
       notes="OT (and recap) 'bread from heaven'/manna, typological echo of 'I am the bread of life'. ot_refs on the Johannine Term use Old Testament hits only.")
    # manna as exact
    rows += exact_words("I AM", ["manna"], subgroup=ot,
                        notes="See bread from heaven / manna.")
    rows += phrases("I AM", [
        "the lord is my light",
        "the lord shall be unto thee an everlasting light",
        "everlasting light",
        "in thy light shall we see light",
        "the lord my god will enlighten",
        "a light to the gentiles",
        "the people that walked in darkness have seen a great light",
    ], subgroup=ot,
       notes="OT God-as-light language echoing 'I am the light of the world'.")
    rows += phrases("I AM", [
        "the gate of the lord",
        "lift up your heads, o ye gates",
        "this is the gate of heaven",
    ], subgroup=ot,
       notes="Selected OT door/gate verses (not every tabernacle door) echoing 'I am the door'.")
    rows += phrases("I AM", [
        "the lord is my shepherd",
        "shepherd of israel",
        "he shall feed his flock like a shepherd",
        "i will feed my flock",
        "i will seek that which was lost",
    ], subgroup=ot,
       notes="OT God-as-shepherd language echoing 'I am the good shepherd'. Not every occurrence of the common noun 'shepherd'.")
    rows += phrases("I AM", [
        "i kill, and i make alive",
        "the lord killeth, and maketh alive",
        "i will open your graves",
        "i know that my redeemer liveth",
    ], subgroup=ot,
       notes="Selected OT life-from-death statements echoing 'I am the resurrection, and the life'.")
    rows += phrases("I AM", [
        "this is the way, walk ye in it",
        "the way of holiness",
        "prepare ye the way of the lord",
        "make straight in the desert a highway",
    ], subgroup=ot,
       notes="Selected OT 'way' verses echoing 'I am the way, the truth, and the life'. Not every 'way of the LORD'.")
    rows += phrases("I AM", [
        "vineyard of the lord",
        "thou hast brought a vine out of egypt",
        "i had planted thee a noble vine",
        "israel is an empty vine",
        "a noble vine",
    ], subgroup=ot,
       notes="OT Israel-as-vineyard/vine language echoing 'I am the true vine'.")
    rows += phrases("I AM", [
        "the lord is my rock",
        "he is the rock",
        "rock of israel",
        "the rock that begat thee",
        "who is a rock save our god",
        "god was their rock",
    ], subgroup=ot,
       notes="OT God-as-Rock titles, included as I AM typological echoes (there is no Johannine 'I am the rock'; 1 Cor 10:4 reads the wilderness Rock as Christ). These verses are also Stones / God as Rock/Stone.")


    # ---------- Alchemist overlap (themes Sara flagged as shared with the Bible) ----------
    # Counted in the KJV, The Economy of God, and The Alchemist.
    ao = "Alchemist overlap"
    rows += exact_words(ao, ["fountain", "fountains", "fount"], subgroup="fountains")
    rows += exact_words(ao, [
        "sheep", "shepherd", "shepherds", "flock", "flocks", "lamb", "lambs",
    ], subgroup="sheep")
    rows += exact_words(ao, ["melchizedek", "melchisedec", "melchisedek"], subgroup="character names")
    rows += phrases(ao, ["king of salem"], subgroup="character names")
    rows += exact_words(ao, ["salem"], subgroup="character names", confidence="medium",
                       notes="Place-name Salem (Jerusalem) in the KJV; the Alchemist's 'king of Salem' / Melchizedek is the intended overlap. Some KJV hits are the place alone.")
    rows += exact_words(ao, ["desert", "deserts"], subgroup="desert")
    rows += exact_words(ao, ["wilderness", "wildernesses"], subgroup="desert", confidence="medium",
                       notes="KJV often says 'wilderness' where modern narrative would say 'desert'; included so the comparison is not just a spelling mismatch.")
    rows += exact_words(ao, ["hunger", "hungry", "hungered", "hungreth", "hungred"], subgroup="hunger")
    rows += phrases(ao, ["an hungred"], subgroup="hunger",
                    notes="KJV idiom for 'hungry'.")
    rows += exact_words(ao, ["journey", "journeys", "journeyed", "journeyeth", "journeying"], subgroup="journey")

    return rows
