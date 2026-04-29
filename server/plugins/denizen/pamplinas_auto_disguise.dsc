# Auto-disguise Pamplinas as Allay on login

pamplinas_auto_disguise:
    type: world
    debug: true
    events:
        on player logs in:
        - if <player.name> == Pamplinas:
            - wait 5t
            - execute as_player "disguise allay"
