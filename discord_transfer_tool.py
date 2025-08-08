import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import discord
import aiohttp
import asyncio
import threading
from datetime import datetime
import json
import os

class DiscordTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Message Transfer Tool - User Account")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.user_token = tk.StringVar()
        self.source_channel_id = tk.StringVar()
        self.webhook_url = tk.StringVar()
        self.is_running = False
        self.client = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration du grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Discord Message Transfer Tool - Compte Utilisateur", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Avertissement
        warning_frame = ttk.Frame(main_frame)
        warning_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        warning_label = ttk.Label(warning_frame, 
                                 text="⚠️ ATTENTION: L'utilisation de tokens utilisateur peut violer les ToS de Discord",
                                 foreground="red", font=("Arial", 10, "bold"))
        warning_label.pack()
        
        # Token Utilisateur
        ttk.Label(main_frame, text="Token Utilisateur Discord:").grid(row=2, column=0, sticky=tk.W, pady=5)
        token_entry = ttk.Entry(main_frame, textvariable=self.user_token, width=50, show="*")
        token_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # ID du salon source
        ttk.Label(main_frame, text="ID Salon Source:").grid(row=3, column=0, sticky=tk.W, pady=5)
        source_entry = ttk.Entry(main_frame, textvariable=self.source_channel_id, width=50)
        source_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # URL Webhook
        ttk.Label(main_frame, text="URL Webhook:").grid(row=4, column=0, sticky=tk.W, pady=5)
        webhook_entry = ttk.Entry(main_frame, textvariable=self.webhook_url, width=50)
        webhook_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Instructions pour obtenir le token
        info_frame = ttk.LabelFrame(main_frame, text="Comment obtenir votre token utilisateur", padding="10")
        info_frame.grid(row=5, column=0, columnspan=2, pady=15, sticky=(tk.W, tk.E))
        
        instructions = """1. Ouvrez Discord dans votre navigateur (pas l'app)
2. Appuyez F12 pour ouvrir les outils de développement
3. Allez dans l'onglet "Network" ou "Réseau"
4. Effectuez une action sur Discord (envoyez un message)
5. Cherchez une requête vers discord.com/api
6. Dans les headers, trouvez "authorization" - c'est votre token"""
        
        ttk.Label(info_frame, text=instructions, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="Démarrer le transfert", 
                                      command=self.start_transfer)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Arrêter", 
                                     command=self.stop_transfer, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Barre de progression
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Zone de logs
        ttk.Label(main_frame, text="Logs:", font=("Arial", 12, "bold")).grid(row=8, column=0, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.log_text.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configuration du redimensionnement
        main_frame.rowconfigure(9, weight=1)
        
    def log_message(self, message):
        """Ajoute un message aux logs avec timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Thread-safe update
        self.root.after(0, lambda: self._update_log(log_entry))
        
    def _update_log(self, message):
        """Met à jour les logs de manière thread-safe"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        
    def validate_inputs(self):
        """Valide les entrées utilisateur"""
        if not self.user_token.get().strip():
            messagebox.showerror("Erreur", "Veuillez entrer un token utilisateur Discord valide")
            return False
            
        if not self.source_channel_id.get().strip().isdigit():
            messagebox.showerror("Erreur", "L'ID du salon source doit être un nombre")
            return False
            
        if not self.webhook_url.get().strip().startswith("https://discord.com/api/webhooks/"):
            messagebox.showerror("Erreur", "L'URL webhook doit être une URL Discord valide")
            return False
            
        return True
        
    def start_transfer(self):
        """Démarre le processus de transfert"""
        if not self.validate_inputs():
            return
        
        # Confirmation supplémentaire pour token utilisateur
        if not messagebox.askyesno("Confirmation", 
                                  "Êtes-vous sûr de vouloir utiliser votre token utilisateur?\n"
                                  "Cela peut violer les conditions d'utilisation de Discord."):
            return
            
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start()
        
        self.log_message("Démarrage du transfert avec compte utilisateur...")
        
        # Lancer le transfert dans un thread séparé
        transfer_thread = threading.Thread(target=self.run_transfer)
        transfer_thread.daemon = True
        transfer_thread.start()
        
    def stop_transfer(self):
        """Arrête le processus de transfert"""
        self.is_running = False
        self.log_message("Arrêt demandé...")
        
    def run_transfer(self):
        """Execute le transfert dans un thread séparé"""
        try:
            # Créer une nouvelle boucle d'événements pour ce thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Exécuter le transfert
            loop.run_until_complete(self.transfer_messages())
            
        except Exception as e:
            self.log_message(f"Erreur: {str(e)}")
        finally:
            # Nettoyer
            self.root.after(0, self.transfer_completed)
            
    def transfer_completed(self):
        """Appelé quand le transfert est terminé"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress.stop()
        
    async def transfer_messages(self):
        """Transfère les messages du salon source vers le webhook"""
        
        # Pour un compte utilisateur, on utilise une approche différente
        messages_transferred = 0
        
        try:
            # Nettoyer le token (supprimer les caractères indésirables)
            clean_token = self.user_token.get().strip().replace('\n', '').replace('\r', '').replace('\t', '')
            
            # Utiliser directement l'API Discord avec aiohttp
            headers = {
                'Authorization': clean_token,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            channel_id = self.source_channel_id.get()
            webhook_url = self.webhook_url.get()
            
            async with aiohttp.ClientSession() as session:
                # Vérifier que le token fonctionne
                async with session.get('https://discord.com/api/v9/users/@me', headers=headers) as resp:
                    if resp.status != 200:
                        self.log_message("❌ Token utilisateur invalide")
                        return
                    
                    user_data = await resp.json()
                    self.log_message(f"Connecté en tant que: {user_data['username']}#{user_data['discriminator']}")
                
                # Récupérer les messages du salon
                self.log_message("Récupération des messages...")
                messages = await self.fetch_all_messages(session, headers, channel_id)
                
                if not messages:
                    self.log_message("Aucun message trouvé ou erreur d'accès au salon")
                    return
                
                self.log_message(f"Total de {len(messages)} messages trouvés")
                
                # Trier les messages par timestamp (plus ancien en premier)
                messages.sort(key=lambda x: x['timestamp'])
                
                # Transférer les messages
                for i, message in enumerate(messages, 1):
                    if not self.is_running:
                        self.log_message("Transfert interrompu par l'utilisateur")
                        break
                        
                    success = await self.send_user_message_via_webhook(session, webhook_url, message)
                    
                    if success:
                        messages_transferred += 1
                        
                        # Log de progression toutes les 10 copies
                        if messages_transferred % 10 == 0:
                            self.log_message(f"Progression: {messages_transferred} messages transférés")
                    
                    # Pause plus longue pour éviter le rate limiting (compte utilisateur)
                    await asyncio.sleep(1.0)
                
                # Message final
                self.log_message(f"✅ Transfert terminé! Total: {messages_transferred} messages transférés")
                
        except Exception as e:
            self.log_message(f"❌ Erreur lors du transfert: {str(e)}")
            
    async def fetch_all_messages(self, session, headers, channel_id):
        """Récupère tous les messages d'un salon via l'API Discord"""
        messages = []
        last_message_id = None
        
        try:
            while True:
                if not self.is_running:
                    break
                    
                # Construire l'URL de l'API
                url = f'https://discord.com/api/v9/channels/{channel_id}/messages?limit=100'
                if last_message_id:
                    url += f'&before={last_message_id}'
                
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        self.log_message(f"Erreur API Discord: {resp.status}")
                        break
                    
                    batch = await resp.json()
                    
                    if not batch:  # Plus de messages
                        break
                    
                    messages.extend(batch)
                    last_message_id = batch[-1]['id']
                    
                    self.log_message(f"Récupéré {len(messages)} messages...")
                    
                    # Pause pour respecter le rate limiting
                    await asyncio.sleep(0.5)
            
            return messages
            
        except Exception as e:
            self.log_message(f"Erreur récupération messages: {str(e)}")
            return []
            
    async def send_user_message_via_webhook(self, session, webhook_url, message_data):
        """Envoie un message via webhook (format API Discord)"""
        try:
            # Extraire les informations du message
            content = message_data.get('content', '')
            author = message_data.get('author', {})
            attachments = message_data.get('attachments', [])
            
            # Préparer les données du webhook
            webhook_data = {
                "content": content,
                "username": author.get('username', 'Utilisateur Inconnu'),
                "avatar_url": f"https://cdn.discordapp.com/avatars/{author.get('id')}/{author.get('avatar')}.png" if author.get('avatar') else None
            }
            
            # Gérer les fichiers/images/GIF
            files_data = []
            if attachments:
                for attachment in attachments:
                    try:
                        async with session.get(attachment['url']) as resp:
                            if resp.status == 200:
                                file_data = await resp.read()
                                files_data.append({
                                    'filename': attachment['filename'],
                                    'data': file_data,
                                    'content_type': attachment.get('content_type', 'application/octet-stream')
                                })
                    except Exception as e:
                        self.log_message(f"Erreur téléchargement fichier {attachment['filename']}: {str(e)}")
            
            # Envoyer via webhook
            if files_data:
                # Avec fichiers
                form_data = aiohttp.FormData()
                form_data.add_field('payload_json', json.dumps(webhook_data))
                
                for i, file_info in enumerate(files_data):
                    form_data.add_field(f'file{i}', file_info['data'], 
                                      filename=file_info['filename'],
                                      content_type=file_info['content_type'])
                
                async with session.post(webhook_url, data=form_data) as resp:
                    if resp.status not in [200, 204]:
                        self.log_message(f"Erreur webhook (avec fichiers): {resp.status}")
                        return False
            else:
                # Sans fichiers - mais seulement si il y a du contenu
                if content.strip():
                    async with session.post(webhook_url, json=webhook_data) as resp:
                        if resp.status not in [200, 204]:
                            self.log_message(f"Erreur webhook: {resp.status}")
                            return False
                else:
                    # Message vide (peut être un embed ou autre), on le compte quand même
                    return True
            
            return True
            
        except Exception as e:
            self.log_message(f"Erreur envoi message: {str(e)}")
            return False

    async def get_user_info(self, session, headers):
        """Récupère les informations de l'utilisateur connecté"""
        try:
            async with session.get('https://discord.com/api/v9/users/@me', headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return None
        except:
            return None

def main():
    """Fonction principale"""
    root = tk.Tk()
    app = DiscordTransferApp(root)
    
    # Gestionnaire de fermeture
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("Quitter", "Un transfert est en cours. Voulez-vous vraiment quitter?"):
                app.stop_transfer()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Message d'avertissement au démarrage
    messagebox.showwarning("Avertissement Important", 
                          "ATTENTION: L'utilisation de tokens utilisateur Discord peut violer "
                          "les Conditions d'Utilisation de Discord et potentiellement "
                          "entraîner la suspension de votre compte.\n\n"
                          "Utilisez cet outil à vos propres risques.")
    
    root.mainloop()

if __name__ == "__main__":
    main()