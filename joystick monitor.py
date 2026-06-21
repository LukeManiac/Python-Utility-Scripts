import pygame

pygame.init()
pygame.joystick.init()

joysticks = []
for i in range(pygame.joystick.get_count()):
    js = pygame.joystick.Joystick(i)
    js.init()
    joysticks.append(js)
    print(f"Detected controller: {js.get_name()}")

axis_state = {}
button_state = {}
hat_state = {}

deadzone = 0.25

while True:
    for event in pygame.event.get():

        # AXIS MOTION
        if event.type == pygame.JOYAXISMOTION:
            js = joysticks[event.joy]
            name = js.get_name()
            axis_id = event.axis
            value = event.value

            key = (event.joy, axis_id)

            # apply deadzone
            if abs(value) < deadzone:
                value = 0

            # only print if state changed meaningfully
            if axis_state.get(key) != value:
                axis_state[key] = value
                if value != 0:
                    print(f"{name} axis_{axis_id} {value:.2f}")

        # BUTTON PRESS / RELEASE
        elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
            js = joysticks[event.joy]
            name = js.get_name()
            key = (event.joy, event.button)

            state = event.type == pygame.JOYBUTTONDOWN

            if button_state.get(key) != state:
                button_state[key] = state
                if state:
                    print(f"{name} button_{event.button} pressed")
                else:
                    print(f"{name} button_{event.button} released")

        # HAT MOTION
        elif event.type == pygame.JOYHATMOTION:
            js = joysticks[event.joy]
            name = js.get_name()
            key = (event.joy, event.hat)

            value = event.value  # (x, y)

            if hat_state.get(key) != value:
                hat_state[key] = value
                if value != (0, 0):
                    print(f"{name} hat_{event.hat} {value}")
                else:
                    print(f"{name} hat_{event.hat} centred")