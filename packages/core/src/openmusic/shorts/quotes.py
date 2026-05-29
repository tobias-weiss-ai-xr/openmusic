"""Curated stoic quotes for short video generation."""
from collections import namedtuple
import random

StoicQuote = namedtuple("StoicQuote", ["text", "author"])

QUOTES: list[StoicQuote] = [
    # Marcus Aurelius
    StoicQuote("The universe is change; our life is what our thoughts make it.", "Marcus Aurelius"),
    StoicQuote("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    StoicQuote("You have power over your mind — not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    StoicQuote("The happiness of your life depends upon the quality of your thoughts.", "Marcus Aurelius"),
    StoicQuote("Waste no more time arguing about what a good man should be. Be one.", "Marcus Aurelius"),
    StoicQuote("The soul becomes dyed with the color of its thoughts.", "Marcus Aurelius"),
    StoicQuote("If you are distressed by anything external, the pain is not due to the thing itself, but to your estimate of it.", "Marcus Aurelius"),
    StoicQuote("When you arise in the morning, think of what a precious privilege it is to be alive — to breathe, to think, to enjoy, to love.", "Marcus Aurelius"),
    # Epictetus
    StoicQuote("No man is free who is not master of himself.", "Epictetus"),
    StoicQuote("It's not what happens to you, but how you react to it that matters.", "Epictetus"),
    StoicQuote("First say to yourself what you would be; then do what you have to do.", "Epictetus"),
    StoicQuote("The key is to keep company only with people who uplift you, whose presence calls forth your best.", "Epictetus"),
    StoicQuote("He who laughs at himself never runs out of things to laugh at.", "Epictetus"),
    # Seneca
    StoicQuote("We suffer more often in imagination than in reality.", "Seneca"),
    StoicQuote("Luck is what happens when preparation meets opportunity.", "Seneca"),
    StoicQuote("It is not that we have a short time to live, but that we waste a lot of it.", "Seneca"),
    StoicQuote("Sometimes even to live is an act of courage.", "Seneca"),
    StoicQuote("The whole future lies in uncertainty: live immediately.", "Seneca"),
    # Zeno of Citium
    StoicQuote("Man conquers the world by conquering himself.", "Zeno of Citium"),
    StoicQuote("We have two ears and one mouth, so we should listen more than we say.", "Zeno of Citium"),
]


def get_random_quote(seed: int | None = None) -> StoicQuote:
    """Return a random quote from the collection."""
    rng = random.Random(seed)
    return rng.choice(QUOTES)


def get_quotes_by_author(author: str) -> list[StoicQuote]:
    """Return all quotes by a given author (case-insensitive)."""
    author_lower = author.lower()
    return [q for q in QUOTES if q.author.lower() == author_lower]
