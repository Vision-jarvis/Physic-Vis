import os
from src.core.config import settings

class VoiceSynthesizer:
    """
    Handles Text-to-Speech generation.
    Primary Provider: ElevenLabs (Official SDK)
    """
    
    def __init__(self, provider: str = "elevenlabs"):
        self.provider = provider
        self.api_key = settings.eleven_labs_api_key
        self.client = None
        
        if self.provider == "elevenlabs" and self.api_key:
            try:
                from elevenlabs.client import ElevenLabs
                self.client = ElevenLabs(api_key=self.api_key)
            except ImportError:
                print("   ⚠️ 'elevenlabs' package not installed. Run `pip install elevenlabs`.")
        
    def synthesize(self, text: str, output_path: str) -> str:
        """
        Generate audio from text.
        """
        if self.provider == "elevenlabs":
            return self._elevenlabs_tts(text, output_path)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
            
    def _elevenlabs_tts(self, text: str, output_path: str) -> str:
        """
        ElevenLabs SDK call.
        """
        if not self.client:
            raise ValueError("ElevenLabs client not initialized (check API Key or install package).")
            
        # Voice ID for "Adam" 
        voice_id = "pNInz6obpgDQGcFmaJgB" 
        
        print(f"   🎙️ Synthesizing with ElevenLabs SDK ({len(text)} chars)...")
        
        try:
            # Generate audio stream
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_flash_v2_5",
                output_format="mp3_44100_128",
            )
            
            # Ensure output dir exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to file
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)
                
            print(f"   ✅ Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ ElevenLabs SDK Error: {e}")
            raise
