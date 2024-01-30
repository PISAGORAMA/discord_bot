import discord
from discord import ui
import datetime as dt
from discord.ext import commands
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from config import *

def database_connection():
    """"
    Veritabanı bağlantısı
    :return db: database objesi
    """

    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred, {'databaseURL' : DatabaseURL})
    db = firestore.client()
    return db

db = database_connection() 

Client = commands.Bot(command_prefix='notFound_register',intents=discord.Intents.all())

register_status_channel = None
register_channel = None
tracked_channel = None


@Client.event
async def on_ready():
    """
    Bot başladığı zaman ilk olarak bu fonksiyon çalışır. kayit_izleme_kanal_id, kayit_durumu_kanal_id, kayit_kanal_id config dosyasından import edildi. 
    Bot her açıldığında beklemekte olan kayıt isteklerini siler, kayıt kanalındaki kayıt olma interaksiyonunu yeniden gönderir.

    :param kayit_durumu_kanal_id: Kayıt olunduktan sonra yöneticinin kabul/red/engel yaptığı kanal ID'si
    :param kayit_kanal_id: Kullanıcıların kayıt oldukları kanal ID'si
    :param kayit_izleme_kanal_id: Yetkililerin kayıtla ilgili yaptıkları işlemden sonra tutulan logların bulunduğu kanal ID'si
    :type kayit_durumu_kanal_id: int
    :type kayit_kanal_id: int
    :type kayit_izleme_kanal_id: int
    """

    docs = db.collection('pending_collection').stream()
    for doc in docs:
        doc.reference.delete()
    
    global register_status_channel
    global register_channel
    global tracked_channel
    register_status_channel = await Client.fetch_channel(kayit_durumu_kanal_id)
    register_channel = await Client.fetch_channel(kayit_kanal_id)
    tracked_channel = await Client.fetch_channel(kayit_izleme_kanal_id)
    
    messages = register_channel.history(limit=None)
    async for message in messages: await message.delete()

    embed = discord.Embed(color=discord.Color.random(),description="***Merhaba, Hoş geldin! Kayıt alma işlemleri otonom hâline getiriyoruz ve iyileştirmeler için üzerinde çalışıyoruz. Senden yapmanı istediğim tek şey adımları düzgün takip etmek olacak sadece bu kadar!***",title="```Unidisco Kayıt Botu v_0.0```")
    embed.add_field(name="`Nasıl Kayıt Olurum?`",value="***Lisans, önlisans öğrencileri için;***\n"
    "` Kırmızı Butona Bas. Bilgilerini Doldur. Kısaltmalarla yazmaya özen göster, üniversiteni tam olarak yaz.\n"
    "Örnek Kayıt Şekli; \n"
    "İsim: Ahmet, Bölüm: İnşaat Müh., Üniversite: İstanbul Üniversitesi\n"
    "İsim: Ayşe, Bölüm: Elektrik-Elek. Müh. Üniversite: Düzce Üniversitesi\n`")
    embed.add_field(name="``"    , value="***Liseli öğrenciler için;***\n"
    "`Mavi Butona Bas. Bilgilerini Doldur. Liseyi Bitirdiysen Eğer Sınıf Bölmesine Mezun Yaz.\n"
    "Örnek Kayıt Şekli;\n"
    "İsim: Ömer, Sınıf: 2\n"
    "İsim: Arda, Sınıf: Mezun`\n\n", inline= True)
    embed.set_footer(text="Herhangi bir sorun dahilinde lütfen yetkililer ile iletişime geç.")
    my_buttons = Buttons()
    
    await register_channel.send(view=my_buttons ,content="",embed=embed)
    print("Bot is ready!")

    try:
        await Client.tree.sync()
    except Exception as error:
        print(error)
    
class Buttons(ui.View):
    """
    Kayıt kanalındaki butonlar ve handler'ları
    """
    def __init__(self):
        super().__init__(timeout=0.0)
        self.button_university = ui.Button(label="Üniversite Kayıt Ol", style=discord.ButtonStyle.red, custom_id="red")
        self.button_high = ui.Button(label="Lise Kayıt Ol", style=discord.ButtonStyle.blurple, custom_id="blurple")
        self.add_item(self.button_university)
        self.add_item(self.button_high)
        self.button_university.callback = self.button_handler_university
        self.button_high.callback = self.button_handler_high

    async def button_handler_university(self, interaction: discord.Interaction):
        await interaction.response.send_modal(University_Model())

    async def button_handler_high(self, interaction: discord.Interaction):
        await interaction.response.send_modal(High_Model())


class University_Model(ui.Modal):
    """
    Üniversite kayıt butonuna tıklandıktan sonra karşılaşılacak form ekranı
    """
    def __init__(self):
        super().__init__(timeout=None,title="Kayıt Ol")
    
    name = ui.TextInput(label = "Ad", style = discord.TextStyle.short, max_length=100,placeholder="Adınızı Giriniz.")
    uni = ui.TextInput(label = "Üniversite", style = discord.TextStyle.short, max_length=100,placeholder="Üniversitenizi Giriniz.")
    dept = ui.TextInput(label = "Bölüm", style = discord.TextStyle.short, max_length=100,placeholder="Bölümünüzü Giriniz.")
    status = "1"
    
    async def on_submit(self, interaction: discord.Interaction):
        if db.collection('block_collection').document(f'{interaction.user.id}').get().exists:
            return await interaction.response.send_message(content="Uygunsuz kayıt girişimi sonucu engellendiniz. Lütfen yöneticilere ulaşın.",ephemeral=True)

        if len(str(self.name) + ' | ' + str(self.dept)) > 32:
            await interaction.user.send(""" Lüten isminizi ve bölümünüzü kısaltıp tekrar kayıt olunuz. 
                        Örnek kullanım 1: İsim: Muhammed Eren, Bölüm: Bilgisayar Programcılığı -> İsim: Eren, Bölüm: Bilgisayar Prog.
                        Örnek kullanım 2: İsim: Can, Bölüm: Moleküler Biyoloji ve Genetik -> İsim: Can, Bölüm: Mol. Biyo. & Gen. 
                                        """)
            return await interaction.response.send_message(content="Kayıt Başarısız.",ephemeral=True)

        if db.collection('pending_collection').document(f'{interaction.user.id}').get().exists:
            await interaction.response.send_message(content="Önceden Başvuru Yaptınız.",ephemeral=True)
        else:
            db.collection('pending_collection').document(f'{interaction.user.id}').set({
                'name': str(self.name)[:100],
                'dep_name': str(self.dept)[:100],
                'uni_name': str(self.uni)[:100],
                'status': str(self.status)[:100]
            })

            embed = discord.Embed(title="```Kullanıcı Verisi```",color=discord.Color.random(seed=403857438928347))
            embed.set_thumbnail(url=interaction.user.avatar)
            embed.add_field(name="```İsim ```\n"
                        "↓",value=f"**{self.name}**")
            embed.add_field(name="```Üniversite Adı ```\n"
                        "↓",value=f"**{self.uni}**")
            embed.add_field(name="```Bölüm ```\n"
                        "↓",value=f"**{self.dept}**")
            embed.add_field(name="```Kullanıcı ```\n"
                        "↓",value= f"<@{interaction.user.id}>")
            embed.add_field(name="```Kullanıcı Hesap Açılış Tarihi ```\n"
                        "↓",value=f"**{interaction.user.created_at.date().day}/{str(interaction.user.created_at.date().month)}/{str(interaction.user.created_at.date().year)}**")
            if ((dt.datetime.now().date()) - (interaction.user.created_at.date())).days > 184 and ((dt.datetime.now().date()) - (interaction.user.created_at.date())).days < 365:
                embed.add_field(name="```Kullanıcı Güvenilirliği ```\n"
                        "↓",value="**Orta**")
            elif ((dt.datetime.now().date()) - (interaction.user.created_at.date())).days > 365:
                embed.add_field(name="```Kullanıcı Güvenilirliği ```\n"
                        "↓",value="**İyi**")
            else:
                embed.add_field(name="Kullanıcı Güvenilirliği \n"
                        "↓",value="**Kötü**")
            pending_user_id = interaction.user.id
            await tracked_channel.send(embed=embed,view=Verifier_Model(pending_user_id))
            await interaction.response.send_message(content="Bilgileriniz alınmıştır.",ephemeral=True)

class High_Model(ui.Modal):
    """
    Lise kayıt butonuna tıklandıktan sonra karşılaşılacak form ekranı
    """
    def __init__(self):
        super().__init__(timeout=None,title="Kayıt Ol")

    name = ui.TextInput(label = "Ad", style = discord.TextStyle.short, max_length=100,placeholder="Adınızı Giriniz.")
    number_class = ui.TextInput(label = "Sınıf", style = discord.TextStyle.short, max_length=100,placeholder="Sınıfınızı Giriniz.")
    status = "0"

    async def on_submit(self, interaction: discord.Interaction):
        if db.collection('block_collection').document(f'{interaction.user.id}').get().exists:
            return await interaction.response.send_message(content="Uygunsuz kayıt girişimi sonucu engellendiniz. Lütfen yöneticilere ulaşın.",ephemeral=True)


        if len(str(self.name) + ' | ' + "Lise") > 32:
            await interaction.user.send(""" Lüten isminizi kısaltıp tekrar kayıt olunuz. 
                        Örnek kullanım 1: İsim: Muhammed Eren -> İsim: Eren
                        Örnek kullanım 2: İsim: Yunus Emre -> İsim: Emre 
                                        """)
            return await interaction.response.send_message(content="Kayıt Başarısız.",ephemeral=True)
        
        if db.collection('pending_collection').document(f'{interaction.user.id}').get().exists:
            return await interaction.response.send_message(content="Önceden Başvuru Yaptınız.",ephemeral=True)
        else:
            db.collection('pending_collection').document(f'{interaction.user.id}').set({
                'name': str(self.name)[:100],
                'number_class': str(self.number_class)[:100],
                'status': str(self.status)[:100]
            })

            embed = discord.Embed(title="```Kullanıcı Verisi```",color=discord.Color.random(seed=403857438928347))
            embed.set_thumbnail(url=interaction.user.avatar)
            embed.add_field(name="```İsim ```\n"
                        "↓",value=f"**{self.name}**")
            embed.add_field(name="```Sınıf ```\n"
                        "↓",value=f"**{self.number_class}**")
            embed.add_field(name="```Kullanıcı ```\n"
                        "↓",value= f"<@{interaction.user.id}>")
            embed.add_field(name="```Kullanıcı Hesap Açılış Tarihi ```\n"
                        "↓",value=f"**{interaction.user.created_at.date().day}/{str(interaction.user.created_at.date().month)}/{str(interaction.user.created_at.date().year)}**")
            if ((dt.datetime.now().date()) - (interaction.user.created_at.date())).days > 184 and ((dt.datetime.now().date()) - (interaction.user.created_at.date())).days < 365:
                embed.add_field(name="```Kullanıcı Güvenilirliği ```\n"
                        "↓",value="**Orta**")
            elif ((dt.datetime.now().date()) - (interaction.user.created_at.date())).days > 365:
                embed.add_field(name="```Kullanıcı Güvenilirliği ```\n"
                        "↓",value="**İyi**")
            else:
                embed.add_field(name="Kullanıcı Güvenilirliği \n"
                        "↓",value="**Kötü**")
            pending_user_id = interaction.user.id
            await tracked_channel.send(embed=embed,view=Verifier_Model(pending_user_id))
            await interaction.response.send_message(content="Bilgileriniz alınmıştır.", ephemeral=True)

class Verifier_Model(ui.View):
    """
    Kayıt olunduktan sonra yetkilinin kaydı onaylaması/reddetmesi/engellemesi butonuna basıldıktan sonra oluşacak interaksiyon
    """
    def __init__(self, pending_user_id):
        super().__init__(timeout=0.0)
        global sunucu_id
        self.button_accept = ui.Button(label="Onayla", style=discord.ButtonStyle.green, custom_id="green")
        self.button_reject = ui.Button(label="Reddet", style=discord.ButtonStyle.red, custom_id="red")
        self.button_block = ui.Button(label="Engelle", style=discord.ButtonStyle.blurple, custom_id="purple")
        #self.rejection_model = ui.Modal(title="a")
        self.add_item(self.button_accept)
        self.add_item(self.button_reject)
        self.add_item(self.button_block)
        self.button_accept.callback = self.button_handler_accepter
        self.button_reject.callback = self.button_handler_rejecter
        self.button_block.callback = self.button_handler_block
        self.pending_user_id = pending_user_id
        self.user = Client.get_guild(sunucu_id).get_member(self.pending_user_id)

    async def button_handler_accepter(self, interaction: discord.Interaction):

        if bool(set([role.name for role in interaction.user.roles]).intersection(set(granted_users))):
            self.button_accept.disabled = True
            self.button_reject.disabled = True
            self.button_block.disabled = True
            pending_doc = db.collection("pending_collection").document(str(self.pending_user_id)).get()
            global sunucu_id
            pending_doc_dict = pending_doc.to_dict()

            if pending_doc_dict == None: #Onay öncesi veritabanından hatayla silindi
                return await self.user.send(content="Bir Hata Oluştu, Lütfen yeniden kayıt olunuz.")
            
            if pending_doc_dict["status"] == "0": #liseliyse
                await self.user.edit(nick= pending_doc_dict["name"] + " | " + pending_doc_dict["number_class"])

                if pending_doc_dict["name"] == "Mezun":
                    await self.user.add_roles(discord.utils.get(Client.get_guild(sunucu_id).roles, name="Mezun Senesi"))
                else:
                    await self.user.add_roles(discord.utils.get(Client.get_guild(sunucu_id).roles, name="Lise"))

                await self.user.remove_roles(discord.utils.get(Client.get_guild(sunucu_id).roles, name="Kayıtsız Öğrenci"))

            if pending_doc_dict["status"] == "1": #uniliyse
                await self.user.edit(nick= pending_doc_dict["name"] + " | " + pending_doc_dict["dep_name"])
                await self.user.remove_roles(discord.utils.get(Client.get_guild(sunucu_id).roles, name="Kayıtsız Öğrenci"))
                
                if pending_doc_dict["uni_name"] in str(Client.get_guild(sunucu_id).roles):
                    await self.user.add_roles(discord.utils.get(Client.get_guild(sunucu_id).roles, name=pending_doc_dict["uni_name"]))
                else:
                    await self.user.add_roles(discord.utils.get(Client.get_guild(sunucu_id).roles, name="Diğer Üniversiteler"))

            await self.user.send(content="Kaydınız alınmıştır, keyifli sohbetler dileriz Sayın " + pending_doc_dict["name"])
            await register_status_channel.send(content=f"Kullanıcı: <@{self.user.id}>, Kayıt Durumu: Başarılı, Kaydı Yapan: <@{interaction.user.id}>")
            db.collection('pending_collection').document(str(self.pending_user_id)).delete()
            return await interaction.response.edit_message(content="Kayıt Onaylandı. ",view=self)
        else:
            await interaction.response.send_message(content="Bunu yapabilecek yetkiniz yok.", ephemeral=True)
    
    async def button_handler_rejecter(self, interaction: discord.Interaction):
        if bool(set([role.name for role in interaction.user.roles]).intersection(set(granted_users))):
            self.button_accept.disabled = True
            self.button_reject.disabled = True
            self.button_block.disabled = True
            db.collection('pending_collection').document(str(self.pending_user_id)).delete()
            return await interaction.response.send_modal(Rejecter_Model(self.pending_user_id, self.user, self))
        else:
            await interaction.response.send_message(content="Bunu yapabilecek yetkiniz yok.", ephemeral=True)
            
    async def button_handler_block(self, interaction: discord.Interaction):
        if bool(set([role.name for role in interaction.user.roles]).intersection(set(granted_users))):
            self.button_accept.disabled = True
            self.button_reject.disabled = True
            self.button_block.disabled = True
            db.collection('pending_collection').document(str(self.pending_user_id)).delete()
            return await interaction.response.send_modal(Block_Model(self.pending_user_id, self.user, self))
        else:
            await interaction.response.send_message(content="Bunu yapabilecek yetkiniz yok.", ephemeral=True)

class Block_Model(ui.Modal):
    """
    Yetkilinin kullanıcının kaydını kalıcı olarak engellemesi sonrası oluşacak interaksiyon
    """
    def __init__(self, rejected_user_id, user, accepter_model):
        super().__init__(timeout=None,title="Kayıt Ol")
        self.rejected_user_id = rejected_user_id
        self.rejected_user = user
        self.accepter_model = accepter_model
    reason = ui.TextInput(label = "Engellenme Sebebi", style = discord.TextStyle.short, max_length=100,placeholder="Lütfen engellenme sebebini açıklayıcı olarak giriniz.")
    
    async def on_submit(self, interaction: discord.Interaction):
        db.collection('block_collection').document(f'{self.rejected_user_id}').set({
            'name': str(self.rejected_user.name)[:100],
            'reason': str(self.reason)[:100]
        })

        await Client.get_guild(sunucu_id).get_member(self.rejected_user_id).send(content=f"Kaydınız engellendi. Engellenme sebebi: {str(self.reason)}")
        await register_status_channel.send(content=f"Kullanıcı: <@{self.rejected_user.id}> kaydı, <@{interaction.user.id}> tarafından engellendi. Sebebi: {self.reason}")
        return await interaction.response.edit_message(content="Kullanıcı Engellendi. ",view=self.accepter_model)

class Rejecter_Model(ui.Modal):
    """
    Yetkilinin kullanıcının kaydını reddetmesi sonrası oluşacak interaksiyon
    """
    def __init__(self, rejected_user_id, user, accepter_model):
        super().__init__(timeout=None,title="Kayıt Ol")
        self.rejected_user_id = rejected_user_id
        self.rejected_user = user
        self.accepter_model = accepter_model
    reason = ui.TextInput(label = "Reddedilme Sebebi", style = discord.TextStyle.short, max_length=100,placeholder="Lütfen reddedilme sebebini açıklayıcı olarak giriniz.")

    async def on_submit(self, interaction: discord.Interaction):
        await Client.get_guild(sunucu_id).get_member(self.rejected_user_id).send(content=f"Kaydınız reddedildi. Reddedilme sebebi: {str(self.reason)}")
        await register_status_channel.send(content=f"Kullanıcı: <@{self.rejected_user.id}>, Kayıt Durumu: Başarısız, Sebebi: {self.reason}, İşlemi Yapan: <@{interaction.user.id}>")
        return await interaction.response.edit_message(content="Kayıt Reddedildi. ",view=self.accepter_model)

@Client.tree.command(name="engelkaldir", description="Girilen IDye sahip kullanicinin kayit banini kaldirir.")
async def engelkaldir(interaction: discord.Interaction, unblock_id: str):
    """
    'engelkaldir' komutu verildikten sonra block_collection silinmesi
    """
    if Client.get_guild(sunucu_id).get_member(interaction.user.id).guild_permissions.administrator:
        user = Client.get_guild(sunucu_id).get_member(int(unblock_id))

        if user != None:
            if db.collection('block_collection').document(unblock_id).get().exists:
                db.collection('block_collection').document(unblock_id).delete()
                await interaction.response.send_message(content=f"<@{unblock_id}> kullanıcısının engeli kaldırıldı.", ephemeral=True)
                await register_status_channel.send(content=f"<@{unblock_id}> kullanıcısının engeli, <@{interaction.user.id}> tarafından kaldırıldı.")
            else:
                await interaction.response.send_message(content=f"<@{unblock_id}> kullancısı engellenenler listesinde değil.", ephemeral=True)

        else:
            await interaction.response.send_message(content=f"Böyle bir kullanıcı sunucuda bulunamadı.", ephemeral=True)
    else:
        await interaction.response.send_message(content="Kullanmak için yetkiniz yok.", ephemeral=True)

@Client.tree.command(name="pending-channel-temizle", description="Track channeli temizler.")
async def trackchannelreset(interaction: discord.Interaction):
    """
    'pending-channel-temizle' komutu verildikten sonra pending_collection silinmesi. Bug ya da bot durması ihtimallerine karşı.
    """
    if Client.get_guild(sunucu_id).get_member(interaction.user.id).guild_permissions.administrator:
        docs = db.collection('pending_collection').stream()
        for doc in docs:
            doc.reference.delete()

        await register_status_channel.send(content=f"Kayit izleme veritabani <@{interaction.user.id}> tarafından temizlendi.")
        await interaction.response.send_message(content=f"Pending veritabanı temizlendi.", ephemeral=True)
    else:
        await interaction.response.send_message(content="Kullanmak için yetkiniz yok.", ephemeral=True)
    
Client.run(bot_token,reconnect=True)