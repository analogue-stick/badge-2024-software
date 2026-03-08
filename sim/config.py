import pygame

# define custom keyboard mapping for the 3-way switches.
# You can use the table at https://www.pygame.org/docs/ref/key.html as
# reference for the correct pygame key constant names.

button_map = {
    "left_jog_left": pygame.K_w,
    "left_press": pygame.K_d,
    "left_jog_right": pygame.K_e,
    "right_jog_left": pygame.K_s,
    "right_press": pygame.K_a,
    "right_jog_right": pygame.K_q,
}
