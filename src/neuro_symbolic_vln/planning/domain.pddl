(define (domain vln-minigrid)
    (:requirements :strips :typing)
    (:types robot heading location key door target)

    (:predicates
        (robot-at ?r - robot ?loc - location)
        (facing ?r - robot ?h - heading)
        (turn-right-of ?from ?to - heading)
        (turn-left-of ?from ?to - heading)
        (front-cell ?from - location ?h - heading ?to - location)
        (passable ?loc - location)
        (key-at ?k - key ?loc - location)
        (door-at ?d - door ?loc - location)
        (handempty ?r - robot)
        (holding ?r - robot ?k - key)
        (door-locked ?d - door)
        (door-open ?d - door)
        (key-opens ?k - key ?d - door)
        (target-at ?t - target ?loc - location)
        (task-satisfied)
    )

    (:action turn-left
        :parameters (?r - robot ?from ?to - heading)
        :precondition (and
            (facing ?r ?from)
            (turn-left-of ?from ?to)
        )
        :effect (and
            (not (facing ?r ?from))
            (facing ?r ?to)
        )
    )

    (:action turn-right
        :parameters (?r - robot ?from ?to - heading)
        :precondition (and
            (facing ?r ?from)
            (turn-right-of ?from ?to)
        )
        :effect (and
            (not (facing ?r ?from))
            (facing ?r ?to)
        )
    )

    (:action move-forward
        :parameters (?r - robot ?from ?to - location ?h - heading)
        :precondition (and
            (robot-at ?r ?from)
            (facing ?r ?h)
            (front-cell ?from ?h ?to)
            (passable ?to)
        )
        :effect (and
            (not (robot-at ?r ?from))
            (robot-at ?r ?to)
        )
    )

    (:action pickup-key
        :parameters (?r - robot ?k - key ?loc ?front - location ?h - heading)
        :precondition (and
            (robot-at ?r ?loc)
            (facing ?r ?h)
            (front-cell ?loc ?h ?front)
            (key-at ?k ?front)
            (handempty ?r)
        )
        :effect (and
            (holding ?r ?k)
            (not (key-at ?k ?front))
            (not (handempty ?r))
        )
    )

    (:action toggle-locked-door
        :parameters (?r - robot ?k - key ?d - door ?loc ?front - location ?h - heading)
        :precondition (and
            (robot-at ?r ?loc)
            (facing ?r ?h)
            (front-cell ?loc ?h ?front)
            (door-at ?d ?front)
            (door-locked ?d)
            (holding ?r ?k)
            (key-opens ?k ?d)
        )
        :effect (and
            (not (door-locked ?d))
            (door-open ?d)
            (passable ?front)
        )
    )

    (:action confirm-goto
        :parameters (?r - robot ?t - target ?from ?target-loc - location ?h - heading)
        :precondition (and
            (robot-at ?r ?from)
            (facing ?r ?h)
            (front-cell ?from ?h ?target-loc)
            (target-at ?t ?target-loc)
        )
        :effect (and
            (task-satisfied)
        )
    )
)