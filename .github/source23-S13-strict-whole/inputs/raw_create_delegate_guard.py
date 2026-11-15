"""Permit only Kokoro0.6.1 create's original same-object internal delegation.

No tokenizer, model, cache, DSP or audio code is replaced. The original bound
create_timed receives its original arguments, including raw pause defaults.
"""
import inspect
import sys

PARAMETERS = ('text', 'voice', 'speed', 'lang', 'is_phonemes', 'trim',
              'sentence_pause', 'clause_pause', 'continuous')


def require(value, message):
    if not value:
        raise AssertionError(message)


def make_guard(native_create, native_create_timed, expected_raw, voice,
               voice_id, state, report):
    """state.active is held only around the authorized original raw create."""
    create_signature = inspect.signature(native_create)
    timed_signature = inspect.signature(native_create_timed)
    require(tuple(create_signature.parameters) == tuple(timed_signature.parameters) == PARAMETERS,
            'Original Kokoro0.6.1 create/delegate signature changed')
    require(getattr(native_create, '__self__', None) is getattr(native_create_timed, '__self__', None)
            and getattr(native_create, '__self__', None) is not None,
            'Raw delegate must belong to the same original model object')
    caller_code = native_create.__func__.__code__

    def normalized(arguments):
        return {key: ('voice_sha1', voice_id(value)) if key == 'voice'
                else (type(value).__name__, value) for key, value in arguments.items()}

    expected = create_signature.bind(expected_raw['text'], voice=voice, speed=.95,
                                     lang='en-us', **expected_raw['kwargs'])
    expected.apply_defaults()
    expected_parameters = normalized(expected.arguments)
    report['original_raw_create_internal_delegate_parameters'] = expected_parameters
    report.setdefault('original_raw_create_internal_delegate_calls', [])

    def guarded_delegate(*args, **kwargs):
        require(state.get('active') is True and sys._getframe(1).f_code is caller_code,
                'Only the authorized original raw create may delegate internally')
        require(state.get('calls', 0) == 0, 'Only one original raw internal delegate is permitted')
        actual = timed_signature.bind(*args, **kwargs)
        actual.apply_defaults()
        require(normalized(actual.arguments) == expected_parameters,
                'Raw internal delegation changed its exact original tuple/defaults')
        state['calls'] = 1
        report['original_raw_create_internal_delegate_calls'].append({
            'same_object': True, 'original_create_caller_code_exact': True,
            'parameters': expected_parameters,
            'is_original_internal_delegate_not_extra_logical_model_call': True})
        return native_create_timed(*args, **kwargs)

    return guarded_delegate
