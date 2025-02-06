import config
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN, ROUND_FLOOR
import telebot
import time

session = HTTP(
    testnet=False,
    api_key=config.api_key,
    api_secret=config.api_secret,
)
# DEFINIR PARAMETROS PARA OPERAR
symbol = input("Ingrese el símbolo (ej. XRP): ").upper() + "USDT"
amount_usdt = Decimal(input("Ingrese el monto en USDT: "))
factor_multiplicador_cantidad = Decimal(input("Ingrese el porcentaje de incremento en cantidad (ej. 40 para 40%): ")) / Decimal('100')
numero_recompras = int(input("Ingrese la cantidad de recompras que deseas: "))
side = "Buy"
factor_multiplicador_distancia = Decimal(input("Ingrese el porcentaje de distancia para cada recompra (ej. 2 para 2%): "))
distancia_porcentaje_tp = Decimal(input("Ingrese el porcentaje de distancia para el Take Profit Total (ej. 1.5 para 1.5%): ")) / Decimal('100')
distancia_porcentaje_tplcd = Decimal(input("Ingrese el porcentaje de distancia para el Take Profit LCD (ej. 0.5 para 0.5%): ")) / Decimal('100')
estado = input("¿Deseas usar Take Profit Total? (Si o No): ").lower()
estado = True if estado == "si" else False
distancia_porcentaje_sl = Decimal(numero_recompras * factor_multiplicador_distancia / 100) + Decimal("0.006")  # % Porcentaje en la distancia para colocar el take profit a un 6% de la ultima recompra
Save_currentprice= {}

print("\nParámetros definidos para operar:")
print(f"Símbolo: {symbol}")
print(f"Monto en USDT: {amount_usdt}")
print(f"Factor multiplicador cantidad: {factor_multiplicador_cantidad * 100}%")
print(f"Número de recompras: {numero_recompras}")
print(f"Lado de la operación: {side}")
print(f"Factor multiplicador distancia: {factor_multiplicador_distancia}%")
print(f"Distancia Take Profit Total: {distancia_porcentaje_tp * 100}%")
print(f"Distancia Take Profit LCD: {distancia_porcentaje_tplcd * 100}%")
print(f"Estado de Take Profit Total: {'Activado' if estado else 'Desactivado'}")

bot_token = config.token_telegram
bot = telebot.TeleBot(bot_token)
chat_id = config.chat_id
def enviar_mensaje_telegram(chat_id, mensaje):
    try:
        bot.send_message(chat_id, mensaje, parse_mode='HTML')
    except Exception as e:
        print(f"No se pudo enviar el mensaje a Telegram: {e}")

def get_current_position(symbol):
    try:
        response_positions = session.get_positions(category="linear", symbol=symbol)
        if response_positions['retCode'] == 0:
            return response_positions['result']['list']
        else:
            print(f"Error al obtener la posición: {response_positions}")
            return None
    except Exception as e:
        print(f"Error al obtener la posición: {e}")
        return None

def get_pnl(symbol):
    closed_orders_response = session.get_closed_pnl(category="linear", symbol=symbol, limit=1)
    closed_orders_list = closed_orders_response['result']['list']

    for order in closed_orders_list:
        pnl_cerrada = float(order['closedPnl'])
        titulo = f"<b> PNL Realizado {symbol} </b>\n\n"
        subtitule = f"💰 PNL 💰: {pnl_cerrada:.2f}$ USDT."
        mensaje_pnl = titulo + subtitule
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_pnl) 
        print(mensaje_pnl)
        
def take_profit(symbol, tp=estado):
    try:
        if not tp:  # Si tp es False o No se debe ejecutar Take Profit
            return
        
        # Obtener la lista de posiciones actuales
        positions_list = get_current_position(symbol)
        if not positions_list or len(positions_list) == 0:
            print(f"No hay posiciones abiertas para {symbol}.")
            return
        
        # Extraer información de la posición
        current_price = Decimal(positions_list[0]['avgPrice'])
        side = positions_list[0]['side']
        side_tp = "Sell" if side == "Buy" else "Buy"

        # Calcular el precio del Take Profit
        distancia_porcentaje_tp_decimal = Decimal(str(distancia_porcentaje_tp))
        if side == "Buy":
            price_tp = adjust_price(symbol, current_price * (Decimal(1) + distancia_porcentaje_tp_decimal))
        elif side == "Sell":
            price_tp = adjust_price(symbol, current_price * (Decimal(1) - distancia_porcentaje_tp_decimal))
        else:
            print(f"No se detecta el lado de la posición {side}")
            return
        
        response_limit_tp = session.place_order(
            category="linear",
            symbol=symbol,
            side=side_tp,
            orderType="Limit",
            qty="0",
            price=str(price_tp),
            reduceOnly=True,
        )
        Mensaje_tp = f"Take Profit para {symbol} colocado con éxito: {response_limit_tp}"
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=Mensaje_tp)
        print(Mensaje_tp)
    except Exception as e:
        print(f"Error en Take_profit para {symbol}: {str(e)}")

        
def take_profit_LCD(symbol, base_asset_qty_final):
    try:
        # Obtener la lista de posiciones actuales
        positions_list = get_current_position(symbol)
        if not positions_list or len(positions_list) == 0:
            print(f"No hay posiciones abiertas para {symbol}.")
            return
        
        # Extraer información de la posición
        current_price = Decimal(positions_list[0]['avgPrice'])
        side = positions_list[0]['side']
        qty_size = Decimal(positions_list[0]['size'])  # Obtener el tamaño de la posición
        if side == "Buy":
            side_tp = "Sell"
        else:
            side_tp = "Buy"

        # Calcular el precio del Take Profit según el lado de la posición
        distancia_porcentaje_tp_decimal = Decimal(str(distancia_porcentaje_tplcd))
        if side == "Buy":
            price_tp = adjust_price(symbol, current_price * (Decimal(1) + distancia_porcentaje_tp_decimal))
        elif side == "Sell":
            price_tp = adjust_price(symbol, current_price * (Decimal(1) - distancia_porcentaje_tp_decimal))
        else:
            print(f"No se detecta el lado de la posición {side}")
            return
        
        # Colocar la orden de Take Profit
        response_limit_tp = session.place_order(
            category="linear",
            symbol=symbol,
            side=side_tp,
            orderType="Limit",
            qty=str(qty_size-base_asset_qty_final),  # Utilizar el tamaño de la posición como qty
            price=str(price_tp),
            reduceOnly=True,
        )
        Mensaje_tp = f"Take Profit Parcial {symbol} colocado con éxito: {response_limit_tp}"
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=Mensaje_tp)
        print(Mensaje_tp)
    except Exception as e:
        print(f"Error en Take_profit para {symbol}: {str(e)}")

def recompras(symbol, base_asset_qty_final, distancia_porcentaje_sl, side):
    try:
        # Obtener la posición actual
        positions_list = get_current_position(symbol)
        if not positions_list:
            print(f"No hay posiciones abiertas para {symbol}.")
            return
        current_price = Decimal(positions_list[0]['avgPrice'])
        # Determinar el Stop Loss basado en el lado de la operación
        if side == "Buy":
            price_sl = adjust_price(symbol, current_price * Decimal(1 - distancia_porcentaje_sl))
        else:
            price_sl = adjust_price(symbol, current_price * Decimal(1 + distancia_porcentaje_sl))
        # Colocar orden de Stop Loss
        stop_loss_order = session.set_trading_stop(
            category="linear",
            symbol=symbol,
            stopLoss=price_sl,
            slTriggerB="IndexPrice",
            tpslMode="Full",
            slOrderType="Market",
        )
        mensaje_sl = f"Stop Loss para {symbol} colocado con éxito: {stop_loss_order}"
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_sl)
        print(mensaje_sl)
        # Iniciar el proceso de recompras escalonadas
        size_nuevo = base_asset_qty_final
        for i in range(1, numero_recompras + 1):
            porcentaje_distancia = Decimal('0.01') * i * factor_multiplicador_distancia
            cantidad_orden = size_nuevo * (1 + factor_multiplicador_cantidad)
            # Ajustar la cantidad al tipo de dato correcto
            if isinstance(size_nuevo, int):
                cantidad_orden = int(cantidad_orden)
            else:
                cantidad_orden = round(cantidad_orden, len(str(size_nuevo).split('.')[1]))
            size_nuevo = cantidad_orden
            # Calcular precio de la orden límite
            if side == "Buy":
                precio_orden_limite = adjust_price(symbol, current_price - (current_price * porcentaje_distancia))
            else:
                precio_orden_limite = adjust_price(symbol, current_price + (current_price * porcentaje_distancia))
            # Colocar la orden de compra/venta limitada
            response_limit_order = session.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                orderType="Limit",
                qty=str(cantidad_orden),
                price=str(precio_orden_limite),
            )
            mensaje_recompras = f"{symbol}: Orden Límite de compra {i} colocada con éxito: {response_limit_order}"
            enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_recompras)
            print(mensaje_recompras)
    except Exception as e:
        print(f"Error en la función recompras: {str(e)}")
def abrir_posicion(symbol, base_asset_qty_final):
    try:
        positions_list = get_current_position(symbol)
        if positions_list and any(Decimal(position['size']) != 0 for position in positions_list):
            print("Ya hay una posición abierta. No se abrirá otra posición.")
            return
        response_market_order = session.place_order(
            category="linear",
            symbol=symbol,
            side=side,
            orderType="Market",
            qty=base_asset_qty_final,
        )
        # Limpiar datos anteriores y guardar nueva información
        positions_list = get_current_position(symbol)  # Actualizar posiciones
        if positions_list and len(positions_list) > 0:
            Save_currentprice[symbol] = Decimal(positions_list[0]['avgPrice'])  # Guardar precio de entrada
        Mensaje_market = f"Orden Market Long en {symbol} abierta con éxito: {response_market_order}"
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=Mensaje_market)
        print(Mensaje_market)
        time.sleep(3)
        take_profit(symbol) # colocar Take profit
        recompras(symbol, base_asset_qty_final, distancia_porcentaje_sl,side) # colocar recompras o reventas
        if response_market_order['retCode'] != 0:
            print("Error al abrir la posición: La orden de mercado no se completó correctamente.")
    except Exception as e:
        print(f"Error al abrir la posición: {e}")
def qty_step(symbol, amount_usdt):
    try:
        tickers = session.get_tickers(symbol=symbol, category="linear")
        for ticker_data in tickers["result"]["list"]:
            last_price = float(ticker_data["lastPrice"])

        last_price_decimal = Decimal(last_price)

        step_info = session.get_instruments_info(category="linear", symbol=symbol)
        qty_step = Decimal(step_info['result']['list'][0]['lotSizeFilter']['qtyStep'])

        base_asset_qty = amount_usdt / last_price_decimal

        qty_step_str = str(qty_step)
        if '.' in qty_step_str:
            decimals = len(qty_step_str.split('.')[1])
            base_asset_qty_final = round(base_asset_qty, decimals)
        else:
            base_asset_qty_final = int(base_asset_qty)

        return base_asset_qty_final
    except Exception as e:
        print(f"Error al calcular la cantidad del activo base: {e}")
        return None

def adjust_price(symbol, price):
    try:
        instrument_info = session.get_instruments_info(category="linear", symbol=symbol)
        tick_size = float(instrument_info['result']['list'][0]['priceFilter']['tickSize'])
        price_scale = int(instrument_info['result']['list'][0]['priceScale'])

        tick_dec = Decimal(f"{tick_size}")
        precision = Decimal(f"{10**price_scale}")
        price_decimal = Decimal(f"{price}")
        adjusted_price = (price_decimal * precision) / precision
        adjusted_price = (adjusted_price / tick_dec).quantize(Decimal('1'), rounding=ROUND_FLOOR) * tick_dec

        return float(adjusted_price)
    except Exception as e:
        print(f"Error al ajustar el precio: {e}")
        return None
    
def monitor(base_asset_qty_final, numero_recompras):
    try:
        while True:  
            try:
                positions_list = get_current_position(symbol)

                if positions_list and any(Decimal(position['size']) != 0 for position in positions_list):  
                    current_price = Decimal(positions_list[0]['avgPrice'])
                    size = Decimal(positions_list[0]['size'])

                    open_orders_response = session.get_open_orders(category="linear", symbol=symbol)
                    open_orders = open_orders_response.get('result', {}).get('list', [])
                    recompras_realizadas = sum(1 for order in open_orders if order.get('orderType') == "Limit")

                    if symbol in Save_currentprice and Save_currentprice[symbol] != current_price:
                        print(f"El precio de entrada para {symbol} ha cambiado. Actualizando Take Profit...")

                        tp_limit_orders = [order for order in open_orders if order.get('orderType') == "Limit" and order.get('reduceOnly') == True]
                        for order in tp_limit_orders:
                            cancel_response = session.cancel_order(category="linear", symbol=symbol, orderId=order['orderId'])
                            if 'result' in cancel_response and cancel_response['result']:
                                print(f"Orden de Take Profit cancelada para {symbol}: {cancel_response}")

                        take_profit_LCD(symbol, base_asset_qty_final)
                        Save_currentprice[symbol] = current_price
                        print(f"Nuevo precio de entrada guardado para {symbol}: {current_price}")

                    time.sleep(15)

                    if size == base_asset_qty_final and recompras_realizadas < numero_recompras:
                        print(f"Tamaño de la posición alcanzado en {symbol}. Cancelando órdenes pendientes...")
                        session.cancel_all_orders(category="linear", symbol=symbol)
                        recompras(symbol, base_asset_qty_final, distancia_porcentaje_sl, side)  
                        take_profit(symbol)
                        get_pnl(symbol)  
                        print(f"Recolocando órdenes límites en {symbol}.")
                
                else:  
                    print("Posición cerrada")
                    session.cancel_all_orders(category="linear", symbol=symbol)
                    closed_orders_response = session.get_closed_pnl(category="linear", symbol=symbol, limit=1)
                    closed_orders_list = closed_orders_response.get('result', {}).get('list', [])

                    if closed_orders_list:
                        pnl_cerrada = float(closed_orders_list[0]['closedPnl'])
                        if pnl_cerrada < 0:  
                            mensaje=f"⚠️ Cerrando en pérdidas en {symbol} PNL: {pnl_cerrada:.2f} . Deteniendo bot."
                            enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje)
                            return  # Detiene la ejecución de la función
                        else:
                            tickers_response = session.get_tickers(symbol=symbol, category="linear")
                            tickers_list = tickers_response.get("result", {}).get("list", [])

                            if tickers_list:
                                last_price = float(tickers_list[0]["lastPrice"])
                
                                if symbol in Save_currentprice and Save_currentprice[symbol] is not None and last_price <= Save_currentprice[symbol]:
                                    mensaje = f"Abriendo nueva posición para {symbol} a precio {last_price}..."
                                    get_pnl(symbol) 
                                    enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje)
                                    print(mensaje)
                                    abrir_posicion(symbol, base_asset_qty_final)
                                else:
                                    print(f"Esperando para abrir nueva posición para {symbol}. El precio actual ({last_price}) tiene que llegar a ({Save_currentprice[symbol]}).")
                    
                time.sleep(5)
            
            except Exception as inner_e:
                print(f"⚠️ Error interno en monitor: {str(inner_e)}")

    except KeyboardInterrupt:
        print("🛑 Monitor detenido manualmente.")

    except Exception as e:
        print(f"⚠️ Error crítico en monitor: {str(e)}")


def main():
    try:
        # Calcular la cantidad de activos basada en el monto en USDT
        base_asset_qty_final = qty_step(symbol, amount_usdt)
        
        if base_asset_qty_final is None:
            print("Error al calcular la cantidad de activos.")
            return
        
        # Abrir posición inicial
        abrir_posicion(symbol, base_asset_qty_final)

        # Iniciar el monitoreo de la posición
        monitor(base_asset_qty_final, numero_recompras)
    
    except Exception as e:
        print(f"Error en la función main: {e}")

# Ejecutar la función main
if __name__ == "__main__":
    main()
