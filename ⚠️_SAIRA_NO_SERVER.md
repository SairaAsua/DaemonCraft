# ⚠️ ADVERTENCIA PARA EKO (Y TODOS LOS AGENTES)

## LA COMPUTADORA DE SAIRA NO TIENE SERVIDOR DE MINECRAFT

**NO INSTALAR MINECRAFT SERVER EN ESTA MÁQUINA.**
**NO CORRER `docker compose up` PARA EL SERVIDOR.**
**NO CREAR SERVICIOS SYSTEMD PARA MINECRAFT.**

### ¿Por qué?
- Esta computadora es el entorno de desarrollo/cli de Saira
- El servidor de Minecraft corre en otra máquina de la red (Nico o Annie)
- Instalar un servidor aquí crearía conflicto, consume recursos, y no es necesario

### ¿Qué hacer en cambio?
1. **Preguntar a Saira** cuál servidor usar:
   - ¿El de Nico? (IP: preguntar)
   - ¿El de Annie? (IP: preguntar)
   - ¿Producción? `mc.daemoncraft.world`

2. **Configurar el bot/cast** para que apunte al servidor correcto via variable de entorno `MINECRAFT_SERVER_HOST`

3. **Solo levantar el BOT** (el agente/bridge), NUNCA el servidor

### Servidores conocidos en la red:
| Servidor | Host | Notas |
|----------|------|-------|
| Local (viejo) | 192.168.20.27 | Posiblemente obsoleto |
| Producción | mc.daemoncraft.world | Público, usar con GEYSER |
| Nico | ??? | PREGUNTAR |
| Annie | ??? | PREGUNTAR |

### Cast activo: Eko Oráculo
- Puerto: 3002
- Modelo: Gemma4 via Ollama @ 10.10.20.1:11434
- Rol: Oráculo del Diseño Humano en Minecraft
- **NO es servidor de Minecraft, es un BOT que se CONECTA a uno**

---
*Si ves este archivo y estás pensando en instalar un servidor de Minecraft aquí, DETENTE. Pregunta primero.*
