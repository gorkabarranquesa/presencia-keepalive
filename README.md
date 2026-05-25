# Keepalive para apps de Streamlit Community Cloud

Workflow de GitHub Actions que mantiene despiertas las apps de presencia
en Streamlit Community Cloud (plan gratuito), donde las apps sin tráfico
durante 12 h se duermen y muestran "This app has gone to sleep".

## Cómo funciona

Cada 8 horas, GitHub Actions arranca un Ubuntu, instala Playwright +
Chromium headless, abre las URLs configuradas, y si la app está
dormida pulsa el botón "Yes, get this app back up!". Si está despierta
simplemente registra "AWAKE" y termina.

Un `curl` o un servicio de uptime estándar **no sirve** porque
Streamlit devuelve un HTML estático con código 200 incluso cuando la
app está dormida — para despertarla hay que ejecutar el JavaScript de
la página, y para eso hace falta un navegador de verdad.

## Setup (una vez)

1. **Crea un repo nuevo en GitHub**, por ejemplo `presencia-keepalive`.
   Puede ser público o privado; si es público, los minutos de GitHub
   Actions son ilimitados, así que mejor público (no hay nada
   sensible aquí dentro).

2. **Sube los dos archivos** de esta carpeta a la raíz del repo,
   respetando rutas:

   ```
   wake_apps.py
   .github/workflows/keepalive.yml
   ```

3. **Configura las URLs a mantener despiertas** como variable del repo:

   - Ve a `Settings → Secrets and variables → Actions → Variables`.
   - Pulsa `New repository variable`.
   - Nombre: `STREAMLIT_URLS`
   - Valor: las URLs separadas por coma, por ejemplo:

     ```
     https://presenciap2.streamlit.app,https://presenciap3.streamlit.app
     ```

   Las URLs son **variables**, no secrets, porque ya son públicas
   (el QR de cualquier visitante las contiene).

4. **Habilita Actions** (si está la primera vez): ve a la pestaña
   `Actions` del repo y, si te lo pide, dale a "I understand my
   workflows, go ahead and enable them".

5. **Lanza una primera ejecución manual** para verificar que todo va:

   - Pestaña `Actions` → en el menú lateral, "Mantener apps Streamlit
     despiertas" → botón `Run workflow` → `Run workflow`.
   - Se ejecutará en uno o dos minutos. Pinchas en la ejecución y en
     el paso "Despertar las apps" deberías ver dos líneas tipo:

     ```
     AWAKE                          https://presenciap2.streamlit.app
     AWAKE                          https://presenciap3.streamlit.app
     ```

     o, si alguna estaba dormida:

     ```
     WOKEN                          https://presenciap2.streamlit.app
     AWAKE                          https://presenciap3.streamlit.app
     ```

A partir de aquí el workflow se ejecuta solo, tres veces al día.

## Ajustar la frecuencia

Edita `cron` en `.github/workflows/keepalive.yml`. Recuerda que GitHub
usa **UTC** (sin cambio horario por DST). Como Streamlit duerme apps
tras 12 h, con dos ejecuciones al día separadas por menos de 12 h ya
bastaría; tres da margen de seguridad.

## Si una app no se despierta

Pinchas en la ejecución del workflow → si ves `ERROR  ...` para esa
URL, copia el mensaje. Causas habituales:

- **Timeout > 60 s al cargar**: la app pudo estar levantándose en ese
  momento. La siguiente ejecución probablemente funcione.
- **La URL ha cambiado**: actualiza el valor de la variable
  `STREAMLIT_URLS` en Settings.
- **Streamlit ha cambiado el texto del botón** "Yes, get this app
  back up!": edita la constante `WAKE_BTN_TEXT` en `wake_apps.py`.
