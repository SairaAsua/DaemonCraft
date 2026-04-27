# DaemonCraft Denizen NPC Scripts
# These are pre-built assignment scripts that Pamplinas can assign to any NPC
# via /npc assign --set <script_name>

# ---------------------------------------------------------------------------
# 1. GREETER — A friendly NPC that welcomes players by name
# ---------------------------------------------------------------------------
dc_greeter:
    type: assignment
    actions:
        on assignment:
        - trigger name:click state:true
        on click:
        - chat "Greetings, <player.name>! I am <npc.name>. Welcome to these lands."
        - narrate "<npc.name> smiles warmly at you."

# ---------------------------------------------------------------------------
# 2. QUEST GIVER — Offers a simple quest with accept/decline
# ---------------------------------------------------------------------------
dc_quest_giver:
    type: assignment
    actions:
        on assignment:
        - trigger name:click state:true
        on click:
        - chat "Adventurer <player.name>! The old ruins east of here hide a dangerous secret."
        - chat "Will you investigate and return with news? Say YES to accept."
        - narrate "<npc.name> looks at you with hopeful eyes."
        - flag player dc_quest_pending:true
        - flag player dc_quest_giver:<npc.id>
        - run dc_quest_giver_interact

# Interact script for chat-based quest acceptance
dc_quest_giver_interact:
    type: interact
    steps:
        1:
            chat trigger:
                1:
                    trigger: /yes|si|accept/
                    script:
                    - if !<player.has_flag[dc_quest_pending]> queue clear
                    - flag player dc_quest_active:true
                    - flag player dc_quest_pending:!
                    - chat "Excellent! May fortune guide your steps, <player.name>."
                    - narrate "Quest accepted: Investigate the old ruins."
                2:
                    trigger: /no|decline|reject/
                    script:
                    - if !<player.has_flag[dc_quest_pending]> queue clear
                    - flag player dc_quest_pending:!
                    - chat "I understand. Should you change your mind, I will be here."

# ---------------------------------------------------------------------------
# 3. LOREKEEPER — Tells a short story when clicked
# ---------------------------------------------------------------------------
dc_lorekeeper:
    type: assignment
    actions:
        on assignment:
        - trigger name:click state:true
        on click:
        - chat "Listen well, <player.name>, for I remember the Before-Time."
        - chat "The sky was whole then, and the ground did not tremble."
        - chat "But the Architects grew proud, and built too high..."
        - narrate "<npc.name>'s voice drops to a whisper."
        - chat "Now only echoes remain. And you, traveler. Only you."

# ---------------------------------------------------------------------------
# 4. WARNER — Warns players of nearby danger
# ---------------------------------------------------------------------------
dc_warner:
    type: assignment
    actions:
        on assignment:
        - trigger name:proximity state:true radius:8
        on proximity:
        - chat "Halt, <player.name>! Danger lurks beyond this point."
        - narrate "<npc.name> raises a warning hand."
