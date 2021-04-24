from wakeword_web import scenarios
import sys
import logging
import time


def main():
    name = sys.argv[1]
    available_scenarios = [i.name for i in scenarios.scenarios]

    try:
        scenario = [i for i in scenarios.scenarios if i.name == name][0]
    except:
        logging.error("No such scenario: %r, available scenarios: %r", name, available_scenarios)
        raise

    print(f"Scenario {scenario.name}: '{scenario.description}'")

    for step in scenario.script:
        if isinstance(step, scenarios.SetPrompt):
            print(f"Set prompt to '{step.prompt}'")
        if isinstance(step, scenarios.Wait):
            print(f"Wait for {step.timeout} sec, cancellable: {bool(step.fast_forward_button)}, annotation label: {step.label}")
            if step.timeout:
                time.sleep(step.timeout)


if __name__ == '__main__':
    main()