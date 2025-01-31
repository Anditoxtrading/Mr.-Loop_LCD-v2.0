# Mr. Loop LCD para Futuros de Bybit

¡Bienvenido al script Mr. Loop LCD para Futuros de Bybit! Este script fue desarrollado para automatizar operaciones de LCD en Bybit, enfocándose exclusivamente en los pares USDT.

## Requisitos Previos

Antes de utilizar el script, asegúrate de tener instalado Python en tu sistema. Se recomienda evitar la última versión de Python para una compatibilidad óptima.

## Configuración

1. Descarga y modifica el archivo `config.py` utilizando un editor de texto como Sublime Text o el Bloc de notas.

2. Agrega tu API KEY y API SECRET proporcionadas por Bybit.

    ```python
    api_key = 'TU_API_KEY'
    api_secret = 'TU_API_SECRET'
    ```

3. Crea un bot en Telegram utilizando [BotFather](https://t.me/BotFather) y agrega el token de tu bot al archivo `config.py`.

    ```python
    token_telegram = 'TU_TOKEN_BOT'
    ```

4. Para encontrar tu Chat ID en Telegram, utiliza [@userdatailsbot](
https://web.telegram.org/a/#6095653659) y agrega el Chat ID al archivo `config.py`.

    ```python
    chat_id = "TU_CHAT_ID"
    ```

## Instalación de Dependencias

Antes de ejecutar el script, instala las librerías de Python de Bybit y Telegram utilizando los siguientes comandos:

    
    pip install pybit
    pip install pyTelegramBotAPI
    

## Notas Importantes

- Este script está diseñado específicamente para la plataforma Bybit.
- Al descargar tendras 2 archivos para el script, uno que dice full, ese tiene la funcion de telegram y el otro que dice Version no telegram, ese solo te envia los mensajes a la consola de python y no utiliza telegram.
- Es posible que si no tienes tu cuenta unificada en Bybit, debido a algunas funciones de la API, el bot presente algún error.
- Si decides utilizar este script, ten en cuenta que no soy un programador profesional. He desarrollado este bot basándome en herramientas disponibles y la documentación de las API de Bybit.
- Se recomienda no dejar todo tu capital en la billetera asociada al bot. Transfiere únicamente los fondos necesarios para operar y considera mover el resto a otra billetera o subcuenta.

## Contacto

¡Espero que disfrutes utilizando Mr. Loop LCD para tus operaciones en Bybit! Si tienes alguna pregunta o sugerencia, no dudes en ponerte en contacto a través del grupo de telegram del bot [Telegram](https://t.me/+sHGMnNWU9RcxYTBh).

¡Buena suerte!



