import itertools
from dataclasses import dataclass, asdict, field
import typing

ref_phrases = [[
    'In the great green room',
    'There was a telephone',
    'A comb with a brush',
    'On top of some kind of bowl full of mush',
    'And a red balloon'
],
    [
        'A picture of the cow jumping over the moon',
        'There were three little bears sitting on chairs',
        'A pair of mittens',
        'Goodnight to the quite old lady whispering hush'
    ]
]


class Step:
    pass

@dataclass
class SetPrompt(Step):
    prompt: str
    #FIXME
    action: str = 'setprompt'
    
@dataclass
class Wait(Step):
    timeout: typing.Optional[int] = None
    label: typing.Optional[str] = None
    fast_forward_button: typing.Optional[str] = None
    # FIXME
    action: str = 'wait'



@dataclass
class RecordingScenario:
    name: str
    description: str
    script: typing.List[Step] = field(default_factory=list)


wake_count = 10

bg_intro = [
    SetPrompt(
        "First, we record background noise. Click next and just wait until timer runs down, don't say anything"),
    Wait(fast_forward_button='next...'),
    SetPrompt("Recording background noise..."),
    Wait(16, label='background_pre'),

]

bg_and_done = [
    SetPrompt("Recording background noise again..."),
    Wait(16, label='background_post'),
    SetPrompt("Congrats! You're done!"),
]


def make_wakeword(count):
    return RecordingScenario(
        'wakeword_%d' % count,
        'Wakeword, %d iterations' % count,
        [
            SetPrompt("This is the wakeword recording session. "),
            Wait(fast_forward_button='next...'),
            *bg_intro,
            SetPrompt(f"Now, let's record your wakeword {wake_count} times. When ready, click next. Then say the "
                      f"wakeword once for every timer countdown"),
            Wait(fast_forward_button='next...'),
            *itertools.chain(*[
                [
                    SetPrompt(f"[{i} of {wake_count}] Say the wakeword"),
                    Wait(3, label=f'wakeword_{i}'),
                ]
                for i in range(wake_count)
            ]),
            *bg_and_done
        ]
    )

def wakeword_variations():

    hows = [
        "a bit faster",
        "a bit slower (remember: no pauses between words!)",
        "in a deeper voice",
        "in a higher pitched voice",
        "in a SLIGHTLY different accent (ie American/British)",
        "in a SLIGHTLY different accent from last time (ie American/British)",
        "a bit louder",
        "a bit quieter",
        "closer or further away from your mic",
    ]


    return RecordingScenario(
        'wakeword_variations',
        'Variations of the wakeword',
        [
            SetPrompt("This is the wakeword variations recording session."),
            Wait(fast_forward_button='next...'),
            *bg_intro,
            *itertools.chain(*[
                [
                    SetPrompt(f'Click "next" and say your wakeword {i}'),
                    Wait(fast_forward_button='next...'),
                    SetPrompt(f'say your wakeword {i}'),
                    Wait(timeout=3, label=f'wakeword_{n}'),
                    SetPrompt(f'say your wakeword {i} again'),
                    Wait(timeout=3, label=f'wakeword_repeat_{n}'),

                ]
                for n, i in enumerate(hows)
            ]),
            *bg_and_done

        ]
    )


scenarios = [
    make_wakeword(16),
    make_wakeword(32),
    make_wakeword(64),
    wakeword_variations(),
]


def to_json_data(script):
    ret = []
    
    for i in script:
        enc = asdict(i)
        enc['action'] = i.__class__.__name__
        ret.append(enc)
        
    return ret
    

