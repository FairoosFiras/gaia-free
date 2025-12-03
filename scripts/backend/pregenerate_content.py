#!/usr/bin/env python3
"""Pre-generate campaigns and characters for quick access."""

import argparse
import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend/src to path for gaia and gaia_private modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gaia_private.agents.generators.campaign_generator import CampaignGeneratorAgent
from gaia_private.agents.generators.character_generator import CharacterGeneratorAgent
from agents import Runner, RunConfig, ModelSettings
from gaia.infra.llm.model_manager import (
    resolve_model,
    get_model_provider_for_resolved_model,
    ModelName,
    PreferredModels,
    retry_with_fallback,
)
from gaia.infra.storage.campaign_object_store import get_pregenerated_content_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Resolve campaign storage path (defaults to repo's campaign_storage directory)
DEFAULT_CAMPAIGN_STORAGE = Path(__file__).resolve().parents[2] / "campaign_storage"
CAMPAIGN_STORAGE_PATH = Path(os.getenv("CAMPAIGN_STORAGE_PATH", str(DEFAULT_CAMPAIGN_STORAGE))).expanduser()

# Output directory for pre-generated content (shared by backend services)
OUTPUT_DIR = CAMPAIGN_STORAGE_PATH / "pregenerated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOCK_FILE = OUTPUT_DIR / ".pregenerate.lock"
LOCK_POLL_INTERVAL = 2.0

# Campaign variations to generate
CAMPAIGN_PROMPTS = [
    {
        "style": "epic fantasy",
        "prompt": "Create an epic high fantasy D&D campaign with heroes saving the world from ancient evil."
    },
    {
        "style": "dark horror",
        "prompt": "Create a dark horror D&D campaign with gothic themes, mystery, and supernatural threats."
    },
    {
        "style": "political intrigue",
        "prompt": "Create a political intrigue D&D campaign with noble houses, espionage, and power struggles."
    },
    {
        "style": "exploration",
        "prompt": "Create an exploration-focused D&D campaign with uncharted lands, ancient ruins, and lost civilizations."
    },
    {
        "style": "pirate adventure",
        "prompt": "Create a swashbuckling pirate D&D campaign with naval battles, treasure hunts, and island mysteries."
    }
]

# Character variations to generate
CHARACTER_PROMPTS = [
    {
        "type": "warrior",
        "prompt": "Create a level 1 D&D character: A brave warrior (Fighter or Barbarian class) with a martial background."
    },
    {
        "type": "rogue",
        "prompt": "Create a level 1 D&D character: A cunning rogue or ranger with skills in stealth and subterfuge."
    },
    {
        "type": "mage",
        "prompt": "Create a level 1 D&D character: A scholarly mage (Wizard or Sorcerer) with arcane knowledge."
    },
    {
        "type": "cleric",
        "prompt": "Create a level 1 D&D character: A devoted cleric or paladin with divine powers."
    },
    {
        "type": "bard",
        "prompt": "Create a level 1 D&D character: A charismatic bard with performance skills and magical abilities."
    },
    {
        "type": "druid",
        "prompt": "Create a level 3 D&D character: A nature-focused druid or ranger with wilderness expertise."
    },
    {
        "type": "warlock",
        "prompt": "Create a level 2 D&D character: A mysterious warlock with a pact to an otherworldly patron."
    },
    {
        "type": "monk",
        "prompt": "Create a level 2 D&D character: A disciplined monk with martial arts mastery."
    },
    {
        "type": "artificer",
        "prompt": "Create a level 3 D&D character: An inventive artificer with magical item expertise."
    },
    {
        "type": "multiclass",
        "prompt": "Create a level 5 D&D character: An experienced adventurer with diverse skills (can be multiclass)."
    }
]


def _load_existing_counts() -> Tuple[int, int]:
    """Return the number of pre-generated campaigns and characters currently stored.

    Checks GCS first (if available), then falls back to local filesystem.
    This ensures Cloud Run deployments recognize existing content in GCS.
    """
    store = get_pregenerated_content_store()

    # Debug: Log GCS configuration
    logger.info("🔍 DEBUG: Checking pregenerated content...")
    logger.info("🔍 DEBUG: GCS enabled: %s", store.gcs_enabled)
    logger.info("🔍 DEBUG: Local pregenerated dir: %s", store._pregenerated_dir)
    logger.info("🔍 DEBUG: CAMPAIGN_STORAGE_PATH: %s", os.getenv("CAMPAIGN_STORAGE_PATH"))
    logger.info("🔍 DEBUG: CAMPAIGN_STORAGE_BUCKET: %s", os.getenv("CAMPAIGN_STORAGE_BUCKET"))
    logger.info("🔍 DEBUG: ENVIRONMENT_NAME: %s", os.getenv("ENVIRONMENT_NAME"))
    logger.info("🔍 DEBUG: K_SERVICE (Cloud Run): %s", os.getenv("K_SERVICE"))

    def _load_count(filename: str, key: str, label: str) -> int:
        # CRITICAL FIX: Changed force_local=True to False to check GCS first
        logger.info("🔍 DEBUG: Fetching %s (will check GCS if enabled)...", filename)
        result = store.fetch_json(filename, force_local=False)

        logger.info("🔍 DEBUG: Fetch result for %s - source: %s, checked_remote: %s",
                   filename, result.source, result.checked_remote)

        payload = result.payload if isinstance(result.payload, dict) else {}
        values = payload.get(key, [])
        count = len(values) if isinstance(values, list) else 0

        if result.source == "gcs":
            logger.info("✅ Found %s %s in GCS", count, label)
        elif result.source == "local":
            if result.checked_remote:
                logger.info("ℹ️ No pregenerated %s found in GCS; using local filesystem", label)
            logger.info("✅ Found %s %s in local filesystem", count, label)
        else:
            if result.checked_remote:
                logger.info("ℹ️ No pregenerated %s found in GCS", label)
            logger.info(
                "ℹ️ No pregenerated %s found locally at %s",
                label,
                store.local_path(filename),
            )
        return count

    campaigns_count = _load_count("campaigns.json", "campaigns", "campaigns")
    characters_count = _load_count("characters.json", "characters", "characters")

    logger.info("🔍 DEBUG: Total counts - campaigns: %s, characters: %s",
               campaigns_count, characters_count)

    return campaigns_count, characters_count


def _acquire_generation_lock(timeout_seconds: int = 600) -> bool:
    """Acquire an exclusive lock to prevent concurrent pre-generation runs."""

    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(str(os.getpid()))
            logger.info("🔒 Acquired pregeneration lock at %s", LOCK_FILE)
            return True
        except FileExistsError:
            if time.monotonic() >= deadline:
                logger.error("⏰ Timed out waiting for pregeneration lock (%s)", LOCK_FILE)
                return False
            logger.info("⏳ Another process is generating content; waiting for lock...")
            time.sleep(LOCK_POLL_INTERVAL)


def _release_generation_lock() -> None:
    """Release the pre-generation lock."""

    try:
        LOCK_FILE.unlink()
        logger.info("🔓 Released pregeneration lock at %s", LOCK_FILE)
    except FileNotFoundError:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.warning("⚠️ Failed to remove pregeneration lock %s: %s", LOCK_FILE, exc)


async def generate_campaigns() -> List[Dict[str, Any]]:
    """Generate multiple campaign variations using the CampaignGeneratorAgent."""
    campaigns = []
    campaign_generator = CampaignGeneratorAgent()

    # Use centralized fallback chain starting with Kimi
    primary_model = PreferredModels.KIMI.value

    for i, prompt_config in enumerate(CAMPAIGN_PROMPTS):
        logger.info(f"Generating campaign {i+1}/{len(CAMPAIGN_PROMPTS)}: {prompt_config['style']}")

        # Define the generation operation
        async def generate_campaign_with_model(model: str, provider) -> Dict[str, Any]:
            """Inner function that generates campaign with a specific model."""
            # Create RunConfig with the provider
            run_config = RunConfig(
                model=model,
                model_provider=provider,
                model_settings=ModelSettings(
                    temperature=campaign_generator.temperature,
                    parallel_tool_calls=False,
                    tool_choice="auto"
                )
            )

            await campaign_generator.ensure_prompt_loaded()
            agent = campaign_generator.as_openai_agent(model_override=model)
            result = await Runner.run(
                agent,
                prompt_config['prompt'],
                run_config=run_config
            )

            if hasattr(result, 'final_output') and result.final_output:
                if hasattr(result.final_output, 'model_dump'):
                    campaign_data = result.final_output.model_dump()
                    campaign_data['style'] = prompt_config['style']

                    # Validate the campaign is actually interesting
                    if (campaign_data.get('title') and
                        campaign_data.get('description') and
                        len(campaign_data.get('description', '')) > 50 and
                        len(campaign_data.get('key_npcs', [])) >= 3):
                        return campaign_data
                    else:
                        # Validation failure - raise to trigger retry
                        raise ValueError("Campaign lacks required detail (title, description, or NPCs)")
                else:
                    raise ValueError("No structured output from model")
            else:
                raise ValueError("No final output from model")

        try:
            # Use automatic retry with fallback
            campaign_data, model_used = await retry_with_fallback(
                model_key=primary_model,
                operation=generate_campaign_with_model,
                max_retries_per_model=2,
                retry_on_validation_failure=True
            )

            campaigns.append(campaign_data)
            logger.info(f"✅ Generated with {model_used}: {campaign_data.get('title')}")

        except Exception as e:
            error_msg = f"Failed to generate campaign {i+1} with all models in fallback chain"
            logger.error(f"❌ {error_msg}: {e}")
            raise RuntimeError(error_msg) from e

    return campaigns

async def generate_characters() -> List[Dict[str, Any]]:
    """Generate multiple character variations using the CharacterGeneratorAgent."""
    characters = []
    character_generator = CharacterGeneratorAgent()

    # Use centralized fallback chain starting with Kimi
    primary_model = PreferredModels.KIMI.value

    for i, prompt_config in enumerate(CHARACTER_PROMPTS):
        logger.info(f"Generating character {i+1}/{len(CHARACTER_PROMPTS)}: {prompt_config['type']}")

        # Define the generation operation
        async def generate_character_with_model(model: str, provider) -> Dict[str, Any]:
            """Inner function that generates character with a specific model."""
            # Create RunConfig with the provider
            run_config = RunConfig(
                model=model,
                model_provider=provider,
                model_settings=ModelSettings(
                    temperature=character_generator.temperature,
                    parallel_tool_calls=False,
                    tool_choice="auto"
                )
            )

            await character_generator.ensure_prompt_loaded()
            agent = character_generator.as_openai_agent(model_override=model)
            result = await Runner.run(
                agent,
                prompt_config['prompt'],
                run_config=run_config
            )

            if hasattr(result, 'final_output') and result.final_output:
                if hasattr(result.final_output, 'model_dump'):
                    character_data = result.final_output.model_dump()
                    character_data['type'] = prompt_config['type']

                    # Apply default visual values if not provided by AI
                    default_visual_values = {
                        'gender': 'non-binary',
                        'facial_expression': 'determined',
                        'build': 'average'
                    }
                    for field, default_value in default_visual_values.items():
                        if not character_data.get(field):
                            character_data[field] = default_value

                    # Validate character has proper name and details
                    name = character_data.get('name', '').strip()
                    backstory = character_data.get('backstory', '').strip()
                    char_class = character_data.get('character_class', '').strip()

                    # Reject invalid names
                    invalid_name = (
                        not name or
                        name.lower().startswith('unnamed') or
                        'tool_call' in name.lower() or
                        '<' in name or '>' in name or  # Reject XML/HTML tags
                        len(name) < 2 or
                        not any(c.isalpha() for c in name)  # Must have at least one letter
                    )

                    if invalid_name:
                        raise ValueError(f"Invalid character name: '{name}'")

                    if not backstory or len(backstory) < 50:
                        raise ValueError(f"Backstory too short ({len(backstory)} chars, need 50+)")

                    if not char_class:
                        raise ValueError("Missing character_class")

                    # All validations passed
                    return character_data
                else:
                    raise ValueError("No structured output from model")
            else:
                raise ValueError("No final output from model")

        try:
            # Use automatic retry with fallback
            character_data, model_used = await retry_with_fallback(
                model_key=primary_model,
                operation=generate_character_with_model,
                max_retries_per_model=2,
                retry_on_validation_failure=True
            )

            characters.append(character_data)
            name = character_data.get('name', 'Unknown')
            char_class = character_data.get('character_class', 'Unknown')
            logger.info(f"✅ Generated with {model_used}: {name} ({char_class})")

        except Exception as e:
            error_msg = f"Failed to generate character {i+1} with all models in fallback chain"
            logger.error(f"❌ {error_msg}: {e}")
            raise RuntimeError(error_msg) from e

    return characters

def save_content(campaigns: List[Dict[str, Any]], characters: List[Dict[str, Any]]):
    """Save pre-generated content to local files and GCS."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    campaigns_data = {
        "campaigns": campaigns,
        "total": len(campaigns)
    }
    characters_data = {
        "characters": characters,
        "total": len(characters)
    }

    store = get_pregenerated_content_store()
    gcs_enabled = store.gcs_enabled

    campaigns_result = store.write_json(campaigns_data, "campaigns.json")
    campaigns_path = store.local_path("campaigns.json")
    if campaigns_result.local_success:
        logger.info("💾 Saved %s campaigns to %s", len(campaigns), campaigns_path)
    else:
        logger.warning("⚠️ Failed to write campaigns to %s", campaigns_path)

    characters_result = store.write_json(characters_data, "characters.json")
    characters_path = store.local_path("characters.json")
    if characters_result.local_success:
        logger.info("💾 Saved %s characters to %s", len(characters), characters_path)
    else:
        logger.warning("⚠️ Failed to write characters to %s", characters_path)

    if not gcs_enabled:
        logger.info("ℹ️ GCS not enabled; skipping cloud upload")
    else:
        if campaigns_result.remote_success:
            logger.info("✅ Uploaded %s campaigns to GCS", len(campaigns))
        else:
            logger.warning("⚠️ Failed to upload campaigns to GCS")

        if characters_result.remote_success:
            logger.info("✅ Uploaded %s characters to GCS", len(characters))
        else:
            logger.warning("⚠️ Failed to upload characters to GCS")

async def generate_content(
    *,
    force: bool = True,
    min_campaigns: int = len(CAMPAIGN_PROMPTS),
    min_characters: int = len(CHARACTER_PROMPTS),
    lock_timeout: int = 600,
) -> bool:
    """Generate and persist pre-generated content.

    Returns:
        True if new content was generated, False if skipped because sufficient
        content already exists.
    """

    logger.info("🔍 DEBUG: generate_content called with force=%s, min_campaigns=%s, min_characters=%s",
               force, min_campaigns, min_characters)

    if not force:
        logger.info("🔍 DEBUG: Not forcing generation - checking existing content...")
        campaigns_count, characters_count = _load_existing_counts()
        if campaigns_count >= min_campaigns and characters_count >= min_characters:
            logger.info(
                "✅ Pregenerated content already present "
                "(campaigns=%s/%s, characters=%s/%s) — skipping generation.",
                campaigns_count, min_campaigns, characters_count, min_characters,
            )
            return False
        else:
            logger.info(
                "⚠️ Insufficient content found (campaigns=%s/%s, characters=%s/%s) - will generate",
                campaigns_count, min_campaigns, characters_count, min_characters,
            )

    lock_acquired = _acquire_generation_lock(timeout_seconds=lock_timeout)
    if not lock_acquired:
        if not force:
            campaigns_count, characters_count = _load_existing_counts()
            if campaigns_count >= min_campaigns and characters_count >= min_characters:
                logger.info(
                    "✅ Pregenerated content became available while waiting "
                    "(campaigns=%s, characters=%s) — skipping generation.",
                    campaigns_count,
                    characters_count,
                )
                return False
        raise RuntimeError(
            f"Unable to acquire pregeneration lock within {lock_timeout} seconds"
        )

    try:
        if not force:
            campaigns_count, characters_count = _load_existing_counts()
            if campaigns_count >= min_campaigns and characters_count >= min_characters:
                logger.info(
                    "✅ Pregenerated content became available while holding the lock "
                    "(campaigns=%s, characters=%s) — skipping generation.",
                    campaigns_count,
                    characters_count,
                )
                return False

        logger.info("🎲 Starting content pre-generation...")

        # Check for API keys
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_claude = bool(os.getenv("ANTHROPIC_API_KEY"))
        has_parasail = bool(os.getenv("PARASAIL_API_KEY"))

        if not any([has_openai, has_claude, has_parasail]):
            logger.warning(
                "⚠️ No API keys found (OPENAI_API_KEY, ANTHROPIC_API_KEY, or PARASAIL_API_KEY)"
            )
            logger.warning("⚠️ Will attempt to use local models only")

        # Generate campaigns
        logger.info("\n📜 Generating campaigns...")
        campaigns = await generate_campaigns()

        # Generate characters
        logger.info("\n🎭 Generating characters...")
        characters = await generate_characters()

        # Save everything
        logger.info("\n💾 Saving content...")
        save_content(campaigns, characters)

        logger.info(
            "\n✅ Pre-generation complete! Generated %s campaigns and %s characters",
            len(campaigns),
            len(characters),
        )
        return True

    except Exception as exc:
        logger.error("\n❌ Pre-generation failed: %s", exc)
        logger.error("Please ensure you have at least one LLM model available:")
        logger.error("- Set PARASAIL_API_KEY for Kimi K2 model")
        logger.error("- Set ANTHROPIC_API_KEY for Claude model")
        logger.error("- Set OPENAI_API_KEY for OpenAI model")
        logger.error("- Or ensure Ollama is running with llama3.1:8b model")
        raise
    finally:
        _release_generation_lock()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Generate pregenerated campaign and character content."
    )
    parser.add_argument(
        "--if-missing",
        action="store_true",
        help="Skip generation when sufficient pregenerated content already exists.",
    )
    parser.add_argument(
        "--min-campaigns",
        type=int,
        default=len(CAMPAIGN_PROMPTS),
        help="Minimum number of campaigns required to skip generation.",
    )
    parser.add_argument(
        "--min-characters",
        type=int,
        default=len(CHARACTER_PROMPTS),
        help="Minimum number of characters required to skip generation.",
    )
    parser.add_argument(
        "--lock-timeout",
        type=int,
        default=600,
        help="Seconds to wait for another generator to finish before failing.",
    )
    return parser.parse_args()


def _run_cli() -> None:
    """Entry-point when invoked from the command line."""

    args = parse_args()
    try:
        generated = asyncio.run(
            generate_content(
                force=not args.if_missing,
                min_campaigns=max(args.min_campaigns, 0),
                min_characters=max(args.min_characters, 0),
                lock_timeout=max(args.lock_timeout, 1),
            )
        )
        if not generated:
            logger.info(
                "ℹ️ Pregenerated content already satisfies thresholds; nothing to do."
            )
    except Exception as exc:  # noqa: BLE001
        logger.error("❌ Pregeneration command failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    _run_cli()
