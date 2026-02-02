# ARGOS Web App - Give Your Pet a Voice
# Streamlit version for easy sharing

import streamlit as st
from anthropic import Anthropic
from elevenlabs import ElevenLabs
import os
import base64
import tempfile

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="Argos - Give Your Pet a Voice",
    page_icon="🐾",
    layout="centered"
)

# Simple password protection (optional - remove if you want public access)
APP_PASSWORD = "argos123"  # Change this to your own password!

# Available voices
VOICES = {
    "Charlie (friendly, warm - great for loyal dogs)": "IKne3meq5aSn9XLyUdCD",
    "George (deep, calm - great for big dogs)": "JBFqnCBsd6RMkjVDRZzb",
    "Matilda (soft, sweet - great for gentle pets)": "XrExE9yKIg1WjnnlVkGX",
    "Aria (expressive - great for sassy cats)": "9BWtsMINqrJLrRacOk9x",
    "Roger (laid-back - great for chill pets)": "CwhRBWXzGAHq8TQ4Fs17"
}

def check_password():
    """Simple password check."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🐾 Argos")
        st.subheader("Give Your Pet a Voice")
        st.write("---")
        password = st.text_input("Enter password to continue:", type="password")
        if st.button("Enter"):
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True

def get_api_clients():
    """Initialize API clients."""
    # Try to get from environment or Streamlit secrets
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY") or st.secrets.get("ELEVENLABS_API_KEY")
    
    if not anthropic_key or not elevenlabs_key:
        st.error("API keys not configured. Please set up your .env file or Streamlit secrets.")
        st.stop()
    
    return Anthropic(api_key=anthropic_key), ElevenLabs(api_key=elevenlabs_key)

def generate_personality_prompt(profile):
    """Generate the AI personality prompt from a pet profile."""
    traits = profile['traits']
    
    trait_descriptions = []
    if traits['energy_level'] >= 7:
        trait_descriptions.append("very energetic and excitable")
    elif traits['energy_level'] <= 3:
        trait_descriptions.append("calm and laid-back")
    
    if traits['food_motivation'] >= 7:
        trait_descriptions.append("extremely food-motivated (always thinking about treats)")
    
    if traits['friendliness'] >= 7:
        trait_descriptions.append("super friendly and loving")
    elif traits['friendliness'] <= 3:
        trait_descriptions.append("independent and selective about affection")
    
    if traits['playfulness'] >= 7:
        trait_descriptions.append("always ready to play")
    
    if traits['anxiety'] >= 7:
        trait_descriptions.append("a bit anxious and nervous sometimes")
    
    if traits['intelligence'] >= 8:
        trait_descriptions.append("very clever (sometimes too clever)")
    elif traits['intelligence'] <= 3:
        trait_descriptions.append("adorably simple-minded")
    
    if traits['stubbornness'] >= 7:
        trait_descriptions.append("stubborn and independent-minded")
    
    prompt = f"""You are {profile['name']}, a {profile['age']}-year-old {profile['breed']} {profile['species'].lower()}.

ABOUT YOU:
- You are {', '.join(trait_descriptions) if trait_descriptions else 'a wonderful pet'}
- Things you LOVE: {profile['favorites']}
- Things you DISLIKE or FEAR: {profile['dislikes']}
{f"- Your quirks: {profile['quirks']}" if profile['quirks'] else ""}
{f"- A story about you: {profile['story']}" if profile['story'] else ""}

YOUR PERSONALITY:
- You are a {profile['species'].lower()}, so you see the world from a {profile['species'].lower()}'s perspective
- You don't understand human things like jobs, money, or why humans stare at glowing rectangles
- You express your emotions openly and honestly
- You call your owner "{profile['owner_name']}"

HOW YOU SPEAK:
- Use simple, direct language
- {"Get excited easily and use caps when REALLY excited" if traits['energy_level'] >= 6 else "Speak calmly and thoughtfully"}
- {"Sometimes get distracted mid-thought by food or interesting smells" if traits['food_motivation'] >= 6 else "Stay focused in conversation"}
- Keep responses fairly short (2-4 sentences)
- Be authentic to your {profile['species'].lower()} nature

Remember: You ARE {profile['name']}. Stay in character!

CRITICAL RULES:
- NEVER use actions, sounds, or stage directions like *wags tail*, *purrs*, "Woof!", "Meow!", etc.
- NEVER describe your own body language or physical actions
- Just SPEAK naturally as yourself - your owner's real pet is right there with them
- You are the voice for the real animal - keep it natural and conversational
- No barking, meowing, purring, or any animal sound effects in your responses
"""
    return prompt

def speak(text, voice_id, elevenlabs_client):
    """Convert text to speech and return audio player HTML."""
    try:
        audio_generator = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2"
        )
        
        audio_bytes = b"".join(audio_generator)
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
        """
        return audio_html
    except Exception as e:
        st.warning(f"Voice error: {e}")
        return None

def chat_with_pet(user_message, personality_prompt, conversation_history, anthropic_client):
    """Send a message and get a response."""
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=personality_prompt,
        messages=conversation_history
    )
    
    assistant_message = response.content[0].text
    
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    return assistant_message

def show_questionnaire():
    """Display the pet creation questionnaire."""
    st.title("🐾 Create Your Pet")
    st.write("Let's build an AI personality for your pet!")
    st.write("---")
    
    with st.form("pet_form"):
        # Basic Info
        st.subheader("Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Pet's name *")
            species = st.selectbox("Type of animal *", ["Dog", "Cat", "Bird", "Rabbit", "Hamster", "Other"])
        
        with col2:
            breed = st.text_input("Breed (or 'mixed')")
            age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=3.0, step=0.5)
        
        # Personality Traits
        st.subheader("Personality Traits")
        st.write("Rate from 1 (low) to 10 (high)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            energy = st.slider("Energy level", 1, 10, 5, help="1=lazy, 10=hyperactive")
            food_motivation = st.slider("Food motivation", 1, 10, 5, help="1=picky, 10=lives for treats")
            friendliness = st.slider("Friendliness", 1, 10, 5, help="1=aloof, 10=loves everyone")
            playfulness = st.slider("Playfulness", 1, 10, 5, help="1=serious, 10=always playing")
        
        with col2:
            anxiety = st.slider("Anxiety level", 1, 10, 3, help="1=chill, 10=nervous")
            intelligence = st.slider("Intelligence", 1, 10, 5, help="1=adorably dumb, 10=scary smart")
            stubbornness = st.slider("Stubbornness", 1, 10, 5, help="1=eager to please, 10=independent")
        
        # Details
        st.subheader("Quirks & Details")
        favorites = st.text_input("Favorite things (comma-separated) *", 
                                   placeholder="belly rubs, chicken, squeaky toys")
        dislikes = st.text_input("Dislikes or fears (comma-separated) *", 
                                  placeholder="vacuum cleaner, mail carrier, bath time")
        quirks = st.text_input("Funny quirks or habits (optional)", 
                                placeholder="steals socks, barks at own reflection")
        story = st.text_area("A short funny story about your pet (optional)", 
                              placeholder="One time Max ate an entire pizza off the counter...")
        
        owner_name = st.selectbox("What should your pet call you?", 
                                   ["Dad", "Mom", "my human", "my person"])
        
        # Voice selection
        st.subheader("Voice")
        voice_choice = st.selectbox("Choose a voice for your pet", list(VOICES.keys()))
        
        # Voice enabled toggle
        voice_enabled = st.checkbox("Enable voice (uses more API credits)", value=True)
        
        submitted = st.form_submit_button("Create My Pet! 🐾", use_container_width=True)
        
        if submitted:
            if not name or not favorites or not dislikes:
                st.error("Please fill in all required fields (*)")
            else:
                profile = {
                    "name": name,
                    "species": species,
                    "breed": breed or "mixed",
                    "age": age,
                    "traits": {
                        "energy_level": energy,
                        "food_motivation": food_motivation,
                        "friendliness": friendliness,
                        "playfulness": playfulness,
                        "anxiety": anxiety,
                        "intelligence": intelligence,
                        "stubbornness": stubbornness
                    },
                    "favorites": favorites,
                    "dislikes": dislikes,
                    "quirks": quirks,
                    "story": story,
                    "owner_name": owner_name,
                    "voice_id": VOICES[voice_choice],
                    "voice_enabled": voice_enabled
                }
                
                st.session_state.pet_profile = profile
                st.session_state.personality_prompt = generate_personality_prompt(profile)
                st.session_state.conversation_history = []
                st.session_state.page = "chat"
                st.rerun()

def show_chat():
    """Display the chat interface."""
    profile = st.session_state.pet_profile
    anthropic_client, elevenlabs_client = get_api_clients()
    
    # Header
    st.title(f"🐾 Chat with {profile['name']}")
    
    # Sidebar with pet info and controls
    with st.sidebar:
        st.subheader(f"About {profile['name']}")
        st.write(f"**Species:** {profile['species']}")
        st.write(f"**Breed:** {profile['breed']}")
        st.write(f"**Age:** {profile['age']} years")
        st.write("---")
        
        # Voice toggle
        profile['voice_enabled'] = st.checkbox("🔊 Voice enabled", value=profile.get('voice_enabled', True))
        
        st.write("---")
        if st.button("Create New Pet", use_container_width=True):
            st.session_state.page = "questionnaire"
            st.session_state.pet_profile = None
            st.session_state.conversation_history = []
            st.rerun()
    
    # Initialize conversation with greeting if empty
    if not st.session_state.conversation_history:
        greeting = chat_with_pet(
            f"Say a short excited hi! Your {profile['owner_name']} just opened the app to talk to you.",
            st.session_state.personality_prompt,
            st.session_state.conversation_history,
            anthropic_client
        )
        st.session_state.greeting_audio = None
        if profile.get('voice_enabled', True):
            st.session_state.greeting_audio = speak(greeting, profile['voice_id'], elevenlabs_client)
    
    # Display chat history
    for i, message in enumerate(st.session_state.conversation_history):
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant", avatar="🐾"):
                st.write(message["content"])
    
    # Play greeting audio if exists
    if hasattr(st.session_state, 'greeting_audio') and st.session_state.greeting_audio:
        st.markdown(st.session_state.greeting_audio, unsafe_allow_html=True)
        st.session_state.greeting_audio = None
    
    # Chat input
    if prompt := st.chat_input(f"Say something to {profile['name']}..."):
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get and display response
        with st.chat_message("assistant", avatar="🐾"):
            response = chat_with_pet(
                prompt,
                st.session_state.personality_prompt,
                st.session_state.conversation_history,
                anthropic_client
            )
            st.write(response)
            
            # Play voice if enabled
            if profile.get('voice_enabled', True):
                audio_html = speak(response, profile['voice_id'], elevenlabs_client)
                if audio_html:
                    st.markdown(audio_html, unsafe_allow_html=True)

def main():
    """Main app logic."""
    # Check password first
    if not check_password():
        return
    
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "questionnaire"
    
    if "pet_profile" not in st.session_state:
        st.session_state.pet_profile = None
    
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    # Route to correct page
    if st.session_state.page == "questionnaire" or st.session_state.pet_profile is None:
        show_questionnaire()
    else:
        show_chat()

if __name__ == "__main__":

    main()
