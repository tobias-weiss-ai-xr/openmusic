"""Curated stoic quotes for short video generation."""
from collections import namedtuple
import random

StoicQuote = namedtuple("StoicQuote", ["text", "author"])

QUOTES: list[StoicQuote] = [
    # ============================================================
    # Marcus Aurelius
    # ============================================================
    StoicQuote("The universe is change; our life is what our thoughts make it.", "Marcus Aurelius"),
    StoicQuote("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    StoicQuote("You have power over your mind — not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    StoicQuote("The happiness of your life depends upon the quality of your thoughts.", "Marcus Aurelius"),
    StoicQuote("Waste no more time arguing about what a good man should be. Be one.", "Marcus Aurelius"),
    StoicQuote("The soul becomes dyed with the color of its thoughts.", "Marcus Aurelius"),
    StoicQuote("If you are distressed by anything external, the pain is not due to the thing itself, but to your estimate of it.", "Marcus Aurelius"),
    StoicQuote("When you arise in the morning, think of what a precious privilege it is to be alive — to breathe, to think, to enjoy, to love.", "Marcus Aurelius"),
    StoicQuote("It is ridiculous not to escape from one's own wickedness, which is possible, but to try to escape from the wickedness of others, which is impossible.", "Marcus Aurelius"),
    StoicQuote("Accept the things to which fate binds you, and love the people with whom fate brings you together.", "Marcus Aurelius"),
    StoicQuote("Everything that happens is as normal and expected as the spring rose or the summer fruit; this is true of sickness, death, slander, intrigue, and all other things that please or trouble the foolish.", "Marcus Aurelius"),
    StoicQuote("How much time have you lost to anger, grief, envy, or pleasure? How little is left to you for yourself.", "Marcus Aurelius"),
    StoicQuote("The object of life is not to be on the side of the majority, but to escape finding oneself in the ranks of the insane.", "Marcus Aurelius"),
    StoicQuote("He who fears death either fears the loss of sensation or a different kind of sensation. But if you lose sensation, you will feel nothing bad; and if you acquire a different kind, you will be a different creature and will not cease to live.", "Marcus Aurelius"),
    StoicQuote("Such as are your habitual thoughts, such also will be the character of your mind; for the soul is dyed by the thoughts.", "Marcus Aurelius"),
    StoicQuote("Do not act as if you had ten thousand years to live. While you live, while it is in your power, be good.", "Marcus Aurelius"),
    StoicQuote("The best revenge is to be unlike him who performed the injury.", "Marcus Aurelius"),
    StoicQuote("Look back over the past, with its changing empires that rose and fell, and you can foresee the future too.", "Marcus Aurelius"),
    StoicQuote("A person's worth is measured by the worth of what they value.", "Marcus Aurelius"),
    StoicQuote("Very little is needed to make a happy life; it is all within yourself, in your way of thinking.", "Marcus Aurelius"),
    StoicQuote("Let it make no difference to you whether you are cold or warm, if you are doing your duty; and whether you are drowsy or well-rested, whether you are ill at ease or well.", "Marcus Aurelius"),
    StoicQuote("The nearer a man comes to a calm mind, the closer he is to strength.", "Marcus Aurelius"),
    StoicQuote("Every moment think steadily as a Roman and a man to do what thou hast in hand with perfect and simple dignity.", "Marcus Aurelius"),
    StoicQuote("When thou hast been compelled by nature to lose your temper, be presently satisfied and do not punish yourself.", "Marcus Aurelius"),
    StoicQuote("Adapt yourself to the things among which your lot has been cast and love the people with whom destiny has brought you together.", "Marcus Aurelius"),
    StoicQuote("Everything we hear is an opinion, not a fact. Everything we see is a perspective, not the truth.", "Marcus Aurelius"),
    StoicQuote("Never let the future disturb you. You will meet it, if you have to, with the same weapons of reason which today arm you against the present.", "Marcus Aurelius"),
    StoicQuote("Confine yourself to the present.", "Marcus Aurelius"),
    StoicQuote("Realize that you are something greater than your body — a mind capable of choosing the best in every situation.", "Marcus Aurelius"),
    StoicQuote("The mind that is anxious about the future is already miserable.", "Marcus Aurelius"),

    # ============================================================
    # Epictetus
    # ============================================================
    StoicQuote("No man is free who is not master of himself.", "Epictetus"),
    StoicQuote("It's not what happens to you, but how you react to it that matters.", "Epictetus"),
    StoicQuote("First say to yourself what you would be; then do what you have to do.", "Epictetus"),
    StoicQuote("The key is to keep company only with people who uplift you, whose presence calls forth your best.", "Epictetus"),
    StoicQuote("He who laughs at himself never runs out of things to laugh at.", "Epictetus"),
    StoicQuote("We cannot choose our external circumstances, but we can always choose how we respond to them.", "Epictetus"),
    StoicQuote("It is impossible for a man to learn what he thinks he already knows.", "Epictetus"),
    StoicQuote("If you want to improve, be content to be thought foolish and stupid.", "Epictetus"),
    StoicQuote("Only the educated are free.", "Epictetus"),
    StoicQuote("No thing is good or bad, but thinking makes it so.", "Epictetus"),
    StoicQuote("He is a wise man who does not grieve for the things which he has not, but rejoices for those which he has.", "Epictetus"),
    StoicQuote("Don't explain your philosophy. Embody it.", "Epictetus"),
    StoicQuote("There is only one way to happiness and that is to cease worrying about things which are beyond the power of our will.", "Epictetus"),
    StoicQuote("If anyone tells you that a certain person speaks ill of you, do not make excuses about what is said of you — answer, 'He does not know me well, or he would not have spoken thus.'", "Epictetus"),
    StoicQuote("Progress is not achieved by luck or accident, but by working on yourself daily.", "Epictetus"),
    StoicQuote("You become what you give your attention to.", "Epictetus"),
    StoicQuote("How long are you going to wait before you demand the best for yourself?", "Epictetus"),
    StoicQuote("Circumstances do not make the man; they reveal him to himself.", "Epictetus"),
    StoicQuote("On the occasion of every accident that befalls you, remember to turn to yourself and ask what power you have for turning it to use.", "Epictetus"),
    StoicQuote("It is not death or hardship that is frightening, but the fear of death or hardship.", "Epictetus"),
    StoicQuote("Freedom is not procured by a full enjoyment of what is desired, but by controlling the desire.", "Epictetus"),
    StoicQuote("Personify and include the actual words of the precept: — bear and forbear.", "Epictetus"),
    StoicQuote("First learn the meaning of what you say, and then speak.", "Epictetus"),
    StoicQuote("Make the best use of what is in your power, and take the rest as it happens.", "Epictetus"),
    StoicQuote("Whatever you would make habitual, practice it; and whatever you would not make habitual, do not practice, but refrain from.", "Epictetus"),
    StoicQuote("It is difficulties that show what men are.", "Epictetus"),
    StoicQuote("Be careful to leave your sons well instructed rather than rich, for the hopes of the instructed are better than the wealth of the ignorant.", "Epictetus"),
    StoicQuote("When you are offended by any person's insolence, consider that you yourself have been insolent to others.", "Epictetus"),
    StoicQuote("Never depend on the admiration of others. There is no strength in it.", "Epictetus"),

    # ============================================================
    # Seneca
    # ============================================================
    StoicQuote("We suffer more often in imagination than in reality.", "Seneca"),
    StoicQuote("Luck is what happens when preparation meets opportunity.", "Seneca"),
    StoicQuote("It is not that we have a short time to live, but that we waste a lot of it.", "Seneca"),
    StoicQuote("Sometimes even to live is an act of courage.", "Seneca"),
    StoicQuote("The whole future lies in uncertainty: live immediately.", "Seneca"),
    StoicQuote("No man was ever wise by chance.", "Seneca"),
    StoicQuote("It is the power of the mind to be unconquerable.", "Seneca"),
    StoicQuote("As is a tale, so is life: not how long it is, but how good it is is what matters.", "Seneca"),
    StoicQuote("True happiness is to enjoy the present, without anxious dependence upon the future.", "Seneca"),
    StoicQuote("The mind that is anxious about the future is miserable.", "Seneca"),
    StoicQuote("Associate with people who are likely to improve you.", "Seneca"),
    StoicQuote("While we wait for life, life passes by.", "Seneca"),
    StoicQuote("Difficulties strengthen the mind, as labor does the body.", "Seneca"),
    StoicQuote("Every new beginning comes from some other beginning's end.", "Seneca"),
    StoicQuote("You must know that the vices that you would blush for, you should avoid.", "Seneca"),
    StoicQuote("He who has great power can lose it; he who has moderate power can lose it; only he who has none is free from the fear of losing.", "Seneca"),
    StoicQuote("A man is as miserable as he thinks he is.", "Seneca"),
    StoicQuote("Until we have begun to go without them, we fail to realize how unnecessary many things are.", "Seneca"),
    StoicQuote("It is not the man who has too little that is poor, but the one who hankers after more.", "Seneca"),
    StoicQuote("The gallows and the noose: the first strangles, the second does not.", "Seneca"),
    StoicQuote("Let us prepare our minds as if we'd come to the very end of life.", "Seneca"),
    StoicQuote("We should not, like sheep, follow the flock, but rather be guided by reason.", "Seneca"),
    StoicQuote("There is no easy way from the earth to the stars.", "Seneca"),
    StoicQuote("Wisdom does not come from knowing what is right, but from doing what is right.", "Seneca"),
    StoicQuote("If a man knows not to which port he sails, no wind is favorable.", "Seneca"),
    StoicQuote("To be always fortunate, and to pass through life without a pang, is to be ignorant of one half of nature.", "Seneca"),
    StoicQuote("Begin at once to live, and count each separate day as a separate life.", "Seneca"),
    StoicQuote("Wealth is the slave of a wise man, the master of a fool.", "Seneca"),
    StoicQuote("He who suffers before it is necessary, suffers more than is necessary.", "Seneca"),
    StoicQuote("Religion is regarded by the common people as true, by the wise as false, and by the rulers as useful.", "Seneca"),

    # ============================================================
    # Zeno of Citium
    # ============================================================
    StoicQuote("Man conquers the world by conquering himself.", "Zeno of Citium"),
    StoicQuote("We have two ears and one mouth, so we should listen more than we say.", "Zeno of Citium"),
    StoicQuote("Happiness is a good flow of life.", "Zeno of Citium"),
    StoicQuote("The well-being of any single person is achieved through the well-being of all.", "Zeno of Citium"),
    StoicQuote("Better to trip with the feet than with the tongue.", "Zeno of Citium"),
    StoicQuote("Nature has given to men one tongue, but two ears, that we may hear from others twice as much as we speak.", "Zeno of Citium"),

    # ============================================================
    # Musonius Rufus
    # ============================================================
    StoicQuote("That which is in accordance with nature is worth choosing for its own sake.", "Musonius Rufus"),
    StoicQuote("Courage is not the absence of fear, but the mastery of it.", "Musonius Rufus"),
    StoicQuote("Since every one of us would rather be happy than miserable, it is clear that we are born to be happy.", "Musonius Rufus"),
    StoicQuote("We start to practice philosophy when we begin to question the reasons for our actions.", "Musonius Rufus"),
    StoicQuote("One who intends to be good must practice virtues, for the road to virtue is one of practice.", "Musonius Rufus"),
    StoicQuote("Exile is not a loss, but a change of place.", "Musonius Rufus"),
    StoicQuote("The chief work of philosophy is to provide a remedy for human suffering.", "Musonius Rufus"),

    # ============================================================
    # Cleanthes
    # ============================================================
    StoicQuote("Lead me, O Zeus, and thou, O Destiny, to wherever I am assigned.", "Cleanthes"),
    StoicQuote("The universe is one great city, and all men are citizens.", "Cleanthes"),
    StoicQuote("Do not seek to have events happen as you want, but want them to happen as they do happen.", "Cleanthes"),
    StoicQuote("God and the universe are one.", "Cleanthes"),
    StoicQuote("Fate guides the willing, and drags along the reluctant.", "Cleanthes"),

    # ============================================================
    # Chrysippus
    # ============================================================
    StoicQuote("There is no reason that the universe should be arranged so that virtue is not ultimately rewarded.", "Chrysippus"),
    StoicQuote("The universe is a single living being, encompassing all living beings within itself.", "Chrysippus"),
    StoicQuote("We do not say that the happy man is a god, but we do say that he is similar to the gods.", "Chrysippus"),
    StoicQuote("A good man is not unused to a setback, but rather setbacks make him stronger.", "Chrysippus"),

    # ============================================================
    # Cicero
    # ============================================================
    StoicQuote("The life of the dead is placed in the memory of the living.", "Cicero"),
    StoicQuote("A room without books is like a body without a soul.", "Cicero"),
    StoicQuote("Gratitude is not only the greatest of virtues, but the parent of all others.", "Cicero"),
    StoicQuote("The authority of those who teach is often an obstacle to those who wish to learn.", "Cicero"),
    StoicQuote("If you have a garden and a library, you have everything you need.", "Cicero"),
    StoicQuote("Times are bad. Children no longer obey their parents, and everyone is writing a book.", "Cicero"),
    StoicQuote("The safety of the people shall be the highest law.", "Cicero"),
    StoicQuote("No one can give you better advice than yourself.", "Cicero"),
    StoicQuote("What sweetness is left in life, if you take away friendship?", "Cicero"),
    StoicQuote("To be ignorant of what occurred before you were born is to remain always a child.", "Cicero"),

    # ============================================================
    # Socrates
    # ============================================================
    StoicQuote("The only true wisdom is in knowing you know nothing.", "Socrates"),
    StoicQuote("An unexamined life is not worth living.", "Socrates"),
    StoicQuote("He who is not contented with what he has, would not be contented with what he would like to have.", "Socrates"),
    StoicQuote("I cannot teach anybody anything. I can only make them think.", "Socrates"),
    StoicQuote("Be kind, for everyone you meet is fighting a hard battle.", "Socrates"),
    StoicQuote("Education is the kindling of a flame, not the filling of a vessel.", "Socrates"),
    StoicQuote("The hottest love has the coldest end.", "Socrates"),
    StoicQuote("Know thyself.", "Socrates"),
    StoicQuote("To find yourself, think for yourself.", "Socrates"),
    StoicQuote("The secret of happiness, you see, is not found in seeking more, but in developing the capacity to enjoy less.", "Socrates"),
    StoicQuote("Let him who would move the world first move himself.", "Socrates"),
    StoicQuote("By all means marry; if you get a good wife, you'll become happy; if you get a bad one, you'll become a philosopher.", "Socrates"),
    StoicQuote("False words are not only evil in themselves, but they infect the soul with evil.", "Socrates"),
    StoicQuote("He is richest who is content with the least, for content is the wealth of nature.", "Socrates"),
    StoicQuote("Beware the barrenness of a busy life.", "Socrates"),

    # ============================================================
    # Plato
    # ============================================================
    StoicQuote("Be kind, for everyone you meet is fighting a harder battle.", "Plato"),
    StoicQuote("The heaviest penalty for declining to rule is to be ruled by someone inferior to yourself.", "Plato"),
    StoicQuote("Wise men speak because they have something to say; fools because they have to say something.", "Plato"),
    StoicQuote("Courage is knowing what not to fear.", "Plato"),
    StoicQuote("The measure of a man is what he does with power.", "Plato"),
    StoicQuote("We can easily forgive a child who is afraid of the dark; the real tragedy of life is when men are afraid of the light.", "Plato"),
    StoicQuote("Only the dead have seen the end of war.", "Plato"),
    StoicQuote("Human behavior flows from three main sources: desire, emotion, and knowledge.", "Plato"),
    StoicQuote("The soul takes nothing with her to the next world but her education and her culture.", "Plato"),
    StoicQuote("Good actions give strength to ourselves and inspire good actions in others.", "Plato"),
    StoicQuote("Music is a moral law. It gives soul to the universe, wings to the mind, flight to the imagination.", "Plato"),
    StoicQuote("Ignorance, the root and stem of all evil.", "Plato"),
    StoicQuote("Opinion is the medium between knowledge and ignorance.", "Plato"),

    # ============================================================
    # Aristotle
    # ============================================================
    StoicQuote("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Aristotle"),
    StoicQuote("Knowing yourself is the beginning of all wisdom.", "Aristotle"),
    StoicQuote("It is the mark of an educated mind to be able to entertain a thought without accepting it.", "Aristotle"),
    StoicQuote("Happiness depends upon ourselves.", "Aristotle"),
    StoicQuote("The more you know, the more you realize you don't know.", "Aristotle"),
    StoicQuote("What is a friend? A single soul dwelling in two bodies.", "Aristotle"),
    StoicQuote("Those who know, do. Those that understand, teach.", "Aristotle"),
    StoicQuote("In the middle of difficulty lies opportunity.", "Aristotle"),
    StoicQuote("The roots of education are bitter, but the fruit is sweet.", "Aristotle"),
    StoicQuote("No great mind has ever existed without a touch of madness.", "Aristotle"),
    StoicQuote("Patience is bitter, but its fruit is sweet.", "Aristotle"),
    StoicQuote("The whole is more than the sum of its parts.", "Aristotle"),
    StoicQuote("It is not enough to win a war; it is more important to organize the peace.", "Aristotle"),
    StoicQuote("Whosoever desires to be first among you, let him be the servant of all.", "Aristotle"),
    StoicQuote("The one exclusive sign of thorough knowledge is the power of teaching.", "Aristotle"),

    # ============================================================
    # Lao Tzu
    # ============================================================
    StoicQuote("The journey of a thousand miles begins with one step.", "Lao Tzu"),
    StoicQuote("When I let go of what I am, I become what I might be.", "Lao Tzu"),
    StoicQuote("Nature does not hurry, yet everything is accomplished.", "Lao Tzu"),
    StoicQuote("The Tao that can be told is not the eternal Tao.", "Lao Tzu"),
    StoicQuote("Knowing others is intelligence; knowing yourself is true wisdom.", "Lao Tzu"),
    StoicQuote("He who knows others is wise; he who knows himself is enlightened.", "Lao Tzu"),
    StoicQuote("In the pursuit of learning, every day something is acquired. In the pursuit of Tao, every day something is dropped.", "Lao Tzu"),
    StoicQuote("When you are content to be simply yourself and don't compare or compete, everybody will respect you.", "Lao Tzu"),
    StoicQuote("The soft overcomes the hard, the weak overcomes the strong.", "Lao Tzu"),
    StoicQuote("At the center of your being you have the answer; you know who you are and you know what you want.", "Lao Tzu"),
    StoicQuote("Silence is a source of great strength.", "Lao Tzu"),
    StoicQuote("He who conquers others is strong; he who conquers himself is mighty.", "Lao Tzu"),
    StoicQuote("A good traveler has no fixed plans and is not intent upon arriving.", "Lao Tzu"),
    StoicQuote("Life is a series of natural and spontaneous changes. Don't resist them — that only creates sorrow. Let reality be reality.", "Lao Tzu"),
    StoicQuote("The wise man does not lay up his own treasures. The more he gives to others, the more he has for his own.", "Lao Tzu"),
    StoicQuote("By letting it go it all gets done. The world is won by those who let it go.", "Lao Tzu"),
    StoicQuote("He who stands on tiptoe is not steady. He who strides cannot maintain the pace.", "Lao Tzu"),
    StoicQuote("The power of intuitive understanding will protect you from harm until the end of your days.", "Lao Tzu"),
    StoicQuote("Do the difficult things while they are easy and do the great things while they are small.", "Lao Tzu"),
    StoicQuote("Because the wise always correct themselves, they have no errors.", "Lao Tzu"),

    # ============================================================
    # Rumi
    # ============================================================
    StoicQuote("The wound is the place where the light enters you.", "Rumi"),
    StoicQuote("What you seek is seeking you.", "Rumi"),
    StoicQuote("Yesterday I was clever, so I wanted to change the world. Today I am wise, so I am changing myself.", "Rumi"),
    StoicQuote("Don't be satisfied with stories, how things have gone with others. Unfold your own myth.", "Rumi"),
    StoicQuote("The quieter you become, the more you can hear.", "Rumi"),
    StoicQuote("Stop acting so small. You are the universe in ecstatic motion.", "Rumi"),
    StoicQuote("Let the beauty of what you love be what you do.", "Rumi"),
    StoicQuote("You are not a drop in the ocean. You are the entire ocean in a drop.", "Rumi"),
    StoicQuote("Out beyond ideas of wrongdoing and rightdoing, there is a field. I'll meet you there.", "Rumi"),
    StoicQuote("Ignore those that make you fearful and sad, that degrade you with their hatred.", "Rumi"),
    StoicQuote("When you do things from your soul, you feel a river moving in you, a joy.", "Rumi"),
    StoicQuote("Love is the bridge between you and everything.", "Rumi"),
    StoicQuote("Raise your words, not your voice. It is rain that grows flowers, not thunder.", "Rumi"),
    StoicQuote("The only lasting beauty is the beauty of the heart.", "Rumi"),
    StoicQuote("Respond to every call that excites your spirit.", "Rumi"),
    StoicQuote("Before death takes away what we are given, we should give away what we are.", "Rumi"),
    StoicQuote("If you are irritated by every rub, how will your mirror be polished?", "Rumi"),
    StoicQuote("Patience is the key to joy.", "Rumi"),
    StoicQuote("I have lived on the lip of insanity, wanting to know reasons, knocking on a door. It opens. I've been knocking from the inside.", "Rumi"),
    StoicQuote("Be melting snow. Wash yourself of yourself.", "Rumi"),

    # ============================================================
    # Friedrich Nietzsche
    # ============================================================
    StoicQuote("He who has a why to live for can bear almost any how.", "Nietzsche"),
    StoicQuote("What does not kill me makes me stronger.", "Nietzsche"),
    StoicQuote("And those who were seen dancing were thought to be insane by those who could not hear the music.", "Nietzsche"),
    StoicQuote("The snake which cannot cast its skin has to die. As well the minds which are prevented from changing their opinions; they cease to be mind.", "Nietzsche"),
    StoicQuote("Whoever fights monsters should see to it that in the process he does not become a monster.", "Nietzsche"),
    StoicQuote("One must still have chaos in oneself to be able to give birth to a dancing star.", "Nietzsche"),
    StoicQuote("There is always some madness in love. But there is also always some reason in madness.", "Nietzsche"),
    StoicQuote("The higher we soar the smaller we appear to those who cannot fly.", "Nietzsche"),
    StoicQuote("Without music, life would be a mistake.", "Nietzsche"),
    StoicQuote("He who would learn to fly one day must first learn to stand and walk and run.", "Nietzsche"),
    StoicQuote("To live is to suffer, to survive is to find some meaning in the suffering.", "Nietzsche"),
    StoicQuote("It is not a lack of love, but a lack of friendship that makes unhappy marriages.", "Nietzsche"),
    StoicQuote("The individual has always had to struggle to keep from being overwhelmed by the tribe.", "Nietzsche"),
    StoicQuote("Blessed are the forgetful, for they get the better even of their blunders.", "Nietzsche"),
    StoicQuote("Doubt as sin. — Christianity has done its utmost to close the circle and declared even doubt to be sin.", "Nietzsche"),
    StoicQuote("Everything matters. Nobody has the right to say that one thing matters more than another.", "Nietzsche"),
    StoicQuote("I am not worried that you have fallen; I am worried that you will not rise.", "Nietzsche"),
    StoicQuote("The only way to deal with an unfree world is to become so absolutely free that your very existence is an act of rebellion.", "Nietzsche"),
    StoicQuote("You have your way. I have my way. As for the right way, the correct way, and the only way, it does not exist.", "Nietzsche"),
    StoicQuote("What is great in man is that he is a bridge and not an end.", "Nietzsche"),

    # ============================================================
    # Albert Camus
    # ============================================================
    StoicQuote("In the depth of winter, I finally learned that within me there lay an invincible summer.", "Camus"),
    StoicQuote("Man is the only creature who refuses to be what he is.", "Camus"),
    StoicQuote("The struggle itself toward the heights is enough to fill a man's heart.", "Camus"),
    StoicQuote("Live to the point of tears.", "Camus"),
    StoicQuote("Autumn is a second spring when every leaf is a flower.", "Camus"),
    StoicQuote("I would rather live my life as if there is a God and die to find out there isn't, than live as if there isn't and die to find out there is.", "Camus"),
    StoicQuote("Freedom is nothing else but a chance to be better.", "Camus"),
    StoicQuote("Nobody realizes that some people expend tremendous energy merely to be normal.", "Camus"),
    StoicQuote("You will never be happy if you continue to search for what happiness consists of.", "Camus"),
    StoicQuote("A man without ethics is a wild beast loosed upon this world.", "Camus"),
    StoicQuote("Those who write clearly have readers, those who write obscurely have commentators.", "Camus"),
    StoicQuote("The only way to deal with an unfree world is to become so absolutely free that your very existence is an act of rebellion.", "Camus"),
    StoicQuote("Real generosity toward the future lies in giving all to the present.", "Camus"),
    StoicQuote("Integrity has no need of rules.", "Camus"),
    StoicQuote("Instead of killing and dying, men should learn to live and let live.", "Camus"),

    # ============================================================
    # Søren Kierkegaard
    # ============================================================
    StoicQuote("Life can only be understood backwards; but it must be lived forwards.", "Kierkegaard"),
    StoicQuote("Anxiety is the dizziness of freedom.", "Kierkegaard"),
    StoicQuote("The most common form of despair is not being who you are.", "Kierkegaard"),
    StoicQuote("Once you label me you negate me.", "Kierkegaard"),
    StoicQuote("To dare is to lose one's footing momentarily. Not to dare is to lose oneself.", "Kierkegaard"),
    StoicQuote("The function of prayer is not to influence God, but rather to change the nature of the one who prays.", "Kierkegaard"),
    StoicQuote("There are two ways to be fooled. One is to believe what isn't true; the other is to refuse to believe what is true.", "Kierkegaard"),
    StoicQuote("Patience is the courage of the soul.", "Kierkegaard"),
    StoicQuote("Faith is the highest passion in a person.", "Kierkegaard"),
    StoicQuote("The tyrant dies and his rule is over; the martyr dies and his rule begins.", "Kierkegaard"),
    StoicQuote("The highest truth is this: that which is genuinely individual is genuinely universal.", "Kierkegaard"),
    StoicQuote("If I am to love someone, I must be able to believe in that person.", "Kierkegaard"),
    StoicQuote("Boredom is the root of all evil.", "Kierkegaard"),
    StoicQuote("I see it all perfectly; there are two possible situations — one can either do this or that. My honest opinion and my friendly advice is this: do it or do not do it — you will regret both.", "Kierkegaard"),
    StoicQuote("A man who as a physical being is always turned toward the outside, seeing what surges up from the world outside, but turned toward the inside — that is what is called self, what is called inwardness.", "Kierkegaard"),

    # ============================================================
    # Henry David Thoreau
    # ============================================================
    StoicQuote("I went to the woods because I wished to live deliberately, to front only the essential facts of life.", "Thoreau"),
    StoicQuote("The mass of men lead lives of quiet desperation.", "Thoreau"),
    StoicQuote("Simplicity, simplicity, simplicity!", "Thoreau"),
    StoicQuote("Rather than love, than money, than fame, give me truth.", "Thoreau"),
    StoicQuote("It's not what you look at that matters, it's what you see.", "Thoreau"),
    StoicQuote("Our life is frittered away by detail. Simplify, simplify.", "Thoreau"),
    StoicQuote("Most men lead lives of quiet desperation and go to the grave with the song still in them.", "Thoreau"),
    StoicQuote("If a man does not keep pace with his companions, perhaps it is because he hears a different drummer.", "Thoreau"),
    StoicQuote("Disobedience is the true foundation of liberty.", "Thoreau"),
    StoicQuote("Things do not change; we change.", "Thoreau"),
    StoicQuote("To affect the quality of the day, that is the highest of arts.", "Thoreau"),
    StoicQuote("You must live in the present, launch yourself on every wave, find your eternity in each moment.", "Thoreau"),
    StoicQuote("The greatest compliment that was ever paid me was when one asked me what I thought, and attended to my answer.", "Thoreau"),
    StoicQuote("What you get by achieving your goals is not as important as what you become by achieving your goals.", "Thoreau"),
    StoicQuote("As you simplify your life, the laws of the universe will be simpler; solitude will not be solitude, nor poverty poverty, nor weakness weakness.", "Thoreau"),

    # ============================================================
    # Ralph Waldo Emerson
    # ============================================================
    StoicQuote("What lies behind us and what lies before us are tiny matters compared to what lies within us.", "Emerson"),
    StoicQuote("To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.", "Emerson"),
    StoicQuote("Do not go where the path may lead; go instead where there is no path and leave a trail.", "Emerson"),
    StoicQuote("The only person you are destined to become is the person you decide to be.", "Emerson"),
    StoicQuote("Nothing can bring you peace but yourself.", "Emerson"),
    StoicQuote("What you do speaks so loudly that I cannot hear what you say.", "Emerson"),
    StoicQuote("The purpose of life is not to be happy. It is to be useful, to be honorable, to be compassionate, to have it make some difference that you have lived and lived well.", "Emerson"),
    StoicQuote("Once you make a decision, the universe conspires to make it happen.", "Emerson"),
    StoicQuote("It is not the length of life, but the depth.", "Emerson"),
    StoicQuote("Our greatest glory is not in never failing, but in rising up every time we fail.", "Emerson"),
    StoicQuote("The wise man in the storm prays to God, not for safety from danger, but for deliverance from fear.", "Emerson"),
    StoicQuote("Happiness is a perfume you cannot pour on others without getting a few drops on yourself.", "Emerson"),
    StoicQuote("Life is a journey, not a destination.", "Emerson"),
    StoicQuote("The secret in education lies in respecting the student.", "Emerson"),
    StoicQuote("Unless you try to do something beyond what you have already mastered, you will never grow.", "Emerson"),

    # ============================================================
    # Buddha (Siddhartha Gautama)
    # ============================================================
    StoicQuote("The mind is everything. What you think you become.", "Buddha"),
    StoicQuote("Three things cannot be long hidden: the sun, the moon, and the truth.", "Buddha"),
    StoicQuote("Peace comes from within. Do not seek it without.", "Buddha"),
    StoicQuote("Holding on to anger is like drinking poison and expecting the other person to die.", "Buddha"),
    StoicQuote("The root of suffering is attachment.", "Buddha"),
    StoicQuote("In the end, only three things matter: how much you loved, how gently you lived, and how gracefully you let go of things not meant for you.", "Buddha"),
    StoicQuote("Do not dwell in the past, do not dream of the future, concentrate the mind on the present moment.", "Buddha"),
    StoicQuote("You, yourself, as much as anybody in the entire universe, deserve your love and affection.", "Buddha"),
    StoicQuote("Health is the greatest gift, contentment the greatest wealth, faithfulness the best relationship.", "Buddha"),
    StoicQuote("No one saves us but ourselves. No one can and no one may. We ourselves must walk the path.", "Buddha"),
    StoicQuote("The way is not in the sky. The way is in the heart.", "Buddha"),
    StoicQuote("Better than a thousand hollow words, is one word that brings peace.", "Buddha"),
    StoicQuote("An insincere and evil friend is more to be feared than a wild beast.", "Buddha"),
    StoicQuote("What we think, we become.", "Buddha"),
    StoicQuote("You will not be punished for your anger, you will be punished by your anger.", "Buddha"),
    StoicQuote("Work out your own salvation. Do not depend on others.", "Buddha"),
    StoicQuote("Even death is not to be feared by one who has lived wisely.", "Buddha"),
    StoicQuote("The only real failure in life is not to be true to the best one knows.", "Buddha"),
    StoicQuote("Every morning we are born again. What we do today is what matters most.", "Buddha"),
    StoicQuote("It is better to conquer yourself than to win a thousand battles.", "Buddha"),

    # ============================================================
    # Confucius
    # ============================================================
    StoicQuote("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    StoicQuote("Real knowledge is to know the extent of one's ignorance.", "Confucius"),
    StoicQuote("By three methods we may learn wisdom: by reflection, which is noblest; by imitation, which is easiest; and by experience, which is the bitterest.", "Confucius"),
    StoicQuote("Our greatest glory is not in never falling, but in rising every time we fall.", "Confucius"),
    StoicQuote("Everything has beauty, but not everyone sees it.", "Confucius"),
    StoicQuote("The man who moves a mountain begins by carrying away small stones.", "Confucius"),
    StoicQuote("Before you embark on a journey of revenge, dig two graves.", "Confucius"),
    StoicQuote("To see what is right and not do it is want of courage.", "Confucius"),
    StoicQuote("Life is really simple, but we insist on making it complicated.", "Confucius"),
    StoicQuote("He who knows all the answers has not been asked all the questions.", "Confucius"),
    StoicQuote("Wheresoever you go, go with all your heart.", "Confucius"),
    StoicQuote("The will to win, the desire to succeed, the urge to reach your full potential... these are the keys that will unlock the door to personal excellence.", "Confucius"),
    StoicQuote("It is easy to hate and it is difficult to love. This is how the whole scheme of things works.", "Confucius"),
    StoicQuote("When you see a good person, think of becoming like them. When you see someone not so good, reflect on your own weak points.", "Confucius"),
    StoicQuote("The superior man is satisfied and joyful; the average man is always full of distress.", "Confucius"),
    StoicQuote("I hear and I forget. I see and I remember. I do and I understand.", "Confucius"),
    StoicQuote("When it is obvious that the goals cannot be reached, don't adjust the goals, adjust the action steps.", "Confucius"),
    StoicQuote("The man who asks a question is a fool for a minute, the man who does not ask is a fool for life.", "Confucius"),
    StoicQuote("Studying without thinking is useless. Thinking without studying is dangerous.", "Confucius"),
    StoicQuote("Silence is a true friend who never betrays.", "Confucius"),

    # ============================================================
    # Additional Stoic & Philosophical Voices
    # ============================================================
    StoicQuote("Fortune favors the bold.", "Virgil"),
    StoicQuote("The fates lead the willing and drag the unwilling.", "Seneca the Elder"),
    StoicQuote("As water reflects the face, so one's life reflects the heart.", "Solomon"),
    StoicQuote("Do not go gentle into that good night. Rage, rage against the dying of the light.", "Dylan Thomas"),
    StoicQuote("We are twice armed if we fight with faith.", "Plato"),
    StoicQuote("The best time to plant a tree was 20 years ago. The second best time is now.", "Proverb"),
    StoicQuote("Your time is limited, so don't waste it living someone else's life.", "Steve Jobs"),
    StoicQuote("I think, therefore I am.", "Descartes"),
    StoicQuote("The unexamined life is not worth living, but the unlived life is not worth examining.", "Goldman"),
    StoicQuote("Character is fate.", "Heraclitus"),
    StoicQuote("No man's knowledge can go beyond his experience.", "Locke"),
    StoicQuote("The world is a book and those who do not travel read only one page.", "Augustine"),
    StoicQuote("Happiness depends upon ourselves.", "Aristotle"),
    StoicQuote("The life of money-making is one undertaken under compulsion, and wealth is evidently not the good we are seeking; for it is merely useful and for the sake of something else.", "Aristotle"),
    StoicQuote("One who thinks too much about what has to be done can be called a person who does nothing at all.", "Cato the Younger"),
    StoicQuote("Virtue is nothing else than right reason.", "Seneca"),
    StoicQuote("No person has the power to have everything they want, but it is in their power not to want what they haven't got.", "Seneca"),
    StoicQuote("It is not because things are difficult that we do not dare; it is because we do not dare that they are difficult.", "Seneca"),
    StoicQuote("Life is like a boat: you must keep moving, or you'll sink.", "Seneca"),
    StoicQuote("To win true freedom, you must be a slave to philosophy.", "Epictetus"),
    StoicQuote("Appearances to the mind are of four kinds. Things either are what they appear to be; or they neither are, nor appear to be; or they are, and do not appear to be; or they are not, and yet appear to be.", "Epictetus"),
    StoicQuote("God is best worshipped by doing good to men.", "Epictetus"),
    StoicQuote("A man should so live that his life shall be a commendation of wisdom.", "Musonius Rufus"),
    StoicQuote("Do not seek to follow in the footsteps of the wise. Seek what they sought.", "Matsuo Basho"),
    StoicQuote("The obstacles in the path are the path.", "Zen Proverb"),
    StoicQuote("Before enlightenment, chop wood, carry water. After enlightenment, chop wood, carry water.", "Zen Proverb"),
    StoicQuote("When you reach the top of the mountain, keep climbing.", "Zen Proverb"),
    StoicQuote("The bamboo that bends is stronger than the oak that resists.", "Japanese Proverb"),
    StoicQuote("Fall seven times, stand up eight.", "Japanese Proverb"),
    StoicQuote("The only true wisdom is in knowing you know nothing.", "Socrates"),
    StoicQuote("An unexamined life is not worth living.", "Socrates"),
    StoicQuote("The journey of a thousand miles begins with one step.", "Lao Tzu"),
    StoicQuote("When I let go of what I am, I become what I might be.", "Lao Tzu"),
    StoicQuote("Nature does not hurry, yet everything is accomplished.", "Lao Tzu"),
    StoicQuote("The Tao that can be told is not the eternal Tao.", "Lao Tzu"),
    StoicQuote("Knowing others is intelligence; knowing yourself is true wisdom.", "Lao Tzu"),
    StoicQuote("He who knows others is wise; he who knows himself is enlightened.", "Lao Tzu"),
    StoicQuote("In the pursuit of learning, every day something is acquired. In the pursuit of Tao, every day something is dropped.", "Lao Tzu"),
    StoicQuote("When you are content to be simply yourself and don't compare or compete, everybody will respect you.", "Lao Tzu"),
    StoicQuote("The soft overcomes the hard, the weak overcomes the strong.", "Lao Tzu"),
    StoicQuote("No man ever steps in the same river twice", "Heraclitus"),
]


def get_quote_for_day(day: int) -> StoicQuote:
    """Return a deterministic quote for a given day of the year (1-365).

    Uses modular indexing so any positive integer maps to a quote.
    """
    return QUOTES[(day - 1) % len(QUOTES)]


def get_random_quote(seed: int | None = None) -> StoicQuote:
    """Return a random quote from the collection."""
    rng = random.Random(seed)
    return rng.choice(QUOTES)


def get_quotes_by_author(author: str) -> list[StoicQuote]:
    """Return all quotes by a given author (case-insensitive)."""
    author_lower = author.lower()
    return [q for q in QUOTES if q.author.lower() == author_lower]