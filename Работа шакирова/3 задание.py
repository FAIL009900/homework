
import random
import sys
import pygame
import pymunk
import pymunk.pygame_util
from pymunk import Vec2d

width, height = 600, 600


collision_types = {
    "ball": 1,
    "brick": 2,
    "bottom": 3,
    "player": 4,
}

    # создание мяча
def spawn_ball(space, position, direction):
    ball_body = pymunk.Body(1, float("inf"))
    ball_body.position = position

    ball_shape = pymunk.Circle(ball_body, 5)
    ball_shape.color = pygame.Color("green")
    ball_shape.elasticity = 1.0
    ball_shape.collision_type = collision_types["ball"]

    ball_body.apply_impulse_at_local_point(Vec2d(*direction))

    # скорость мяча на статическом уровне
    def constant_velocity(body, gravity, damping, dt):
        body.velocity = body.velocity.normalized() * 400

    ball_body.velocity_func = constant_velocity

    space.add(ball_body, ball_shape)

def setup_level(space, player_body):

    # удаление шариков и кирпичей
    for s in space.shapes[:]:
        if s.body.body_type == pymunk.Body.DYNAMIC and s.body not in [player_body]:
            space.remove(s.body, s)

    # создание мяча
    spawn_ball(
        space, player_body.position + (0, 40), random.choice([(1, 10), (-1, 10)])
    )

    # создание кирпичей
    for x in range(0, 21):
        x = x * random.randint(0, 20) + 70
        for y in range(0, 5):
            y = y * random.randint(0,20) + 250
            brick_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            brick_body.position = x, y
            brick_shape = pymunk.Poly.create_box(brick_body, (20, 10))
            brick_shape.elasticity = 1.0
            brick_shape.color = pygame.Color("blue")
            brick_shape.group = 1
            brick_shape.collision_type = collision_types["brick"]
            space.add(brick_body, brick_shape)

    # удаление кирпичей при столкновении с мячом
    def remove_brick(arbiter, space, data):
        brick_shape = arbiter.shapes[0]
        space.remove(brick_shape, brick_shape.body)

    h = space.add_collision_handler(collision_types["brick"], collision_types["ball"])
    h.separate = remove_brick



def main():
    ### запуск Pygame
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    running = True
    font = pygame.font.SysFont("Arial", 16)
    ### Физика
    space = pymunk.Space()
    pymunk.pygame_util.positive_y_is_up = True
    draw_options = pymunk.pygame_util.DrawOptions(screen)

    ### игровая зона
    # стены - левые-верхние-правые стены
    static_lines = [
        pymunk.Segment(space.static_body, (50, 50), (50, 550), 2),
        pymunk.Segment(space.static_body, (50, 550), (550, 550), 2),
        pymunk.Segment(space.static_body, (550, 550), (550, 50), 2),
    ]
    for line in static_lines:
        line.color = pygame.Color("lightgray")
        line.elasticity = 1.0

    space.add(*static_lines)

    # Датчик, который удаляет все, что к нему прикасается 
    bottom = pymunk.Segment(space.static_body, (50, 50), (550, 50), 2)
    bottom.sensor = True
    bottom.collision_type = collision_types["bottom"]
    bottom.color = pygame.Color("red")

    def remove_first(arbiter, space, data):
        ball_shape = arbiter.shapes[0]
        space.remove(ball_shape, ball_shape.body)
        return True

    h = space.add_collision_handler(collision_types["ball"], collision_types["bottom"])
    h.begin = remove_first
    space.add(bottom)

    ### Корабль игрока
    player_body = pymunk.Body(500, float("inf"))
    player_body.position = 300, 100

    player_shape = pymunk.Segment(player_body, (-50, 0), (50, 0), 8)
    player_shape.color = pygame.Color("red")
    player_shape.elasticity = 1.0
    player_shape.collision_type = collision_types["player"]

    def pre_solve(arbiter, space, data):
        # Нормальное столкновение с кирпичами и направление отскока
        set_ = arbiter.contact_point_set
        if len(set_.points) > 0:
            player_shape = arbiter.shapes[0]
            width = (player_shape.b - player_shape.a).x
            delta = (player_shape.body.position - set_.points[0].point_a).x
            normal = Vec2d(0, 1).rotated(delta / width / 2)
            set_.normal = normal
            set_.points[0].distance = 0
        arbiter.contact_point_set = set_
        return True

    h = space.add_collision_handler(collision_types["player"], collision_types["ball"])
    h.pre_solve = pre_solve

    # ограничение движение игрока прямой линией
    move_joint = pymunk.GrooveJoint(
        space.static_body, player_body, (100, 100), (500, 100), (0, 0)
    )
    space.add(player_body, player_shape, move_joint)
    global state
    # Начать игру
    setup_level(space, player_body)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and (
                event.key in [pygame.K_ESCAPE, pygame.K_q]
            ):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                pygame.image.save(screen, "breakout.png")
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                player_body.velocity = (-600, 0)
            elif event.type == pygame.KEYUP and event.key == pygame.K_LEFT:
                player_body.velocity = 0, 0

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                player_body.velocity = (600, 0)
            elif event.type == pygame.KEYUP and event.key == pygame.K_RIGHT:
                player_body.velocity = 0, 0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                spawn_ball(
                    space,
                    player_body.position + (0, 40),
                    random.choice([(1, 10), (-1, 10)]),
                )

        ### очистить экран
        screen.fill(pygame.Color("black"))

        ### объект
        space.debug_draw(draw_options)

        state = []
        for x in space.shapes:
            s = "%s %s %s" % (x, x.body.position, x.body.velocity)
            state.append(s)

        ### физика
        fps = 60
        dt = 1.0 / fps
        space.step(dt)

        ### информация и откидной экран
        screen.blit(
            font.render("fps: " + str(clock.get_fps()), 1, pygame.Color("white")),
            (0, 0),
        )
        screen.blit(
            font.render(
                "Нажимай стрелки лево-вправо, чтобы двигать платформу",
                1,
                pygame.Color("darkgrey"),
            ),
            (5, height - 35),
        )

        screen.blit(
            font.render(
                "Нажми ESC или Q для выхода из игры", 1, pygame.Color("darkgrey")
            ),
            (5, height - 20),
        )

        pygame.display.flip()
        clock.tick(fps)


if __name__ == "__main__":
    sys.exit(main())