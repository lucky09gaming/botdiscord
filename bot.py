import discord
from discord.ext import commands
import requests
import math
from datetime import datetime

# ==========================================================
# KONFIGURASI
# ==========================================================
TOKEN = 'MTUwOTE2NDYxMTg3NjY4Mzk3Nw.GdTmFG.L39kPg1KaQbOeT-N_M8xgHlFc98IERk1l1KsKk' 
WA_LINK = 'https://discord.com/users/941381774003564615'

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

server_cache = {}

# ==========================================================
# FUNGSI PENCARIAN SERVER (SMART DISCOVERY)
# ==========================================================
def find_server_ip(server_name):
    # 1. Prioritas Utama: Daftar Manual (IME, INTER, IDP)
    manual_list = {
        "ime": "main.imeroleplay.com:30120",
        "inter": "inter.imeroleplay.com:30120",
        "idp": "idp-roleplay.com:30120"
    }
    if server_name.lower() in manual_list:
        return manual_list[server_name.lower()]

    # 2. Logic khusus untuk Indopride (Multi-Endpoint)
    if "indopride" in server_name.lower():
        endpoints = [f"kota{i}.indopride.id" if i > 1 else "kota.indopride.id" for i in range(1, 8)]
        for host in endpoints:
            try:
                if requests.get(f"http://{host}:30120/info.json", timeout=1).status_code == 200:
                    return f"{host}:30120"
            except: continue
            
    # 3. API Publik (Auto-Discover untuk server lain)
    if server_name.lower() in server_cache: return server_cache[server_name.lower()]
    
    try:
        url = "https://servers-frontend.fivem.net/api/mirrors/proxies/lambda/servers/raw"
        res = requests.get(url, timeout=5).json()
        for s in res:
            if server_name.lower() in s['Data']['hostname'].lower():
                ip = s['ConnectEndPoints'][0]
                server_cache[server_name.lower()] = ip
                return ip
    except: return None
    return None

# ==========================================================
# UI PAGINATION (PROFESSIONAL LOOK)
# ==========================================================
class PlayerPaginator(discord.ui.View):
    def __init__(self, data_list, keyword, total, server_name):
        super().__init__(timeout=300)
        self.data_list, self.keyword, self.total, self.server_name = data_list, keyword, total, server_name
        self.page, self.items_per_page = 0, 15
        self.max_pages = math.ceil(len(data_list) / self.items_per_page)
        self.add_item(discord.ui.Button(label="Hubungi Admin", url=WA_LINK, style=discord.ButtonStyle.link, row=1))

    def get_embed(self):
        embed = discord.Embed(title="✅ Hasil Pencarian Pemain", color=discord.Color.green(), timestamp=datetime.now())
        embed.description = f"Server: `{self.server_name}`\nTotal terdeteksi: **{self.total}** | Keyword: `{self.keyword}`\n━━━━━━━━━━━━━━━━━━━━━━━━━━"
        start = self.page * self.items_per_page
        items = self.data_list[start : start + self.items_per_page]
        val = "".join([f"{start+i+1}. **{p['name']}** [ID: {p['id']}] | 🟢 {p.get('ping',0)}ms\n" for i, p in enumerate(items)])
        embed.add_field(name="Daftar Pemain", value=val or "Kosong", inline=False)
        embed.set_footer(text=f"Page {self.page+1}/{self.max_pages} | © 2026 Lucky - IC. UCOK UCOK")
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, row=0)
    async def prev(self, i: discord.Interaction, b: discord.ui.Button):
        self.page -= 1
        await i.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary, row=0)
    async def next(self, i: discord.Interaction, b: discord.ui.Button):
        self.page += 1
        await i.response.edit_message(embed=self.get_embed(), view=self)

# ==========================================================
# COMMANDS
# ==========================================================
@bot.tree.command(name="cari", description="Cari pemain di server manapun")
async def cari(interaction: discord.Interaction, nama_server: str, nama_pemain: str):
    await interaction.response.send_message("⏳ *Melacak server di database...*")
    ip = find_server_ip(nama_server)
    if not ip: return await interaction.edit_original_response(content="❌ Server tidak ditemukan.")
    
    try:
        players = requests.get(f"http://{ip}/players.json", timeout=5).json()
        hasil = [p for p in players if nama_pemain.lower() in p['name'].lower()]
        if not hasil: return await interaction.edit_original_response(content="❌ Pemain tidak ditemukan.")
        
        view = PlayerPaginator(hasil, nama_pemain, len(hasil), ip)
        await interaction.edit_original_response(content=None, embed=view.get_embed(), view=view)
    except: await interaction.edit_original_response(content="❌ Server offline atau menolak koneksi.")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot Ready Bosq!")

bot.run(TOKEN)
