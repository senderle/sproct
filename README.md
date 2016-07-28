# **Sproct**
**`sproct`** is a word-counting script for comparing differences between scripts, transcripts, 
prompt books -- anything that can be represented as a set of lines spoken by different
characters. Its name is short for **S**hakespeare **Pro**mptbook Word **C**oun**t**er.

Sproct was initially developed to analyze differences between performances of *Hamlet* as recorded
in different working scripts from the late nineteenth and early twentieth centuries.

It reads plays that are formatted like this:

> BERNARDO
>
>Who's there?
>
>FRANCISCO
>
>Nay, answer me:-stand, and unfold yourself.
>
>BERNARDO
>
>Long live the king!
>
>FRANCISCO
>
>Bernardo?
>
>BERNARDO
>
>He.
>
>FRANCISCO
>
>You come most carefully upon your hour.
>
>BERNARDO
>
>'Tis now struck twelve; get thee to bed, Francisco.
>
>FRANCISCO
>
>For this relief, much thanks:-'tis bitter cold,
>And I am sick at heart.

## Usage

### Sproct provides three commands, `count`, `diff`, and `bobsim`. 

**`count`** counts the number of words spoken by a character in a given play.

```
usage: sproct.py count [-h] [--character CHARACTER] text

positional arguments:
  text                  The play text file.

optional arguments:
  -h, --help            show this help message and exit
  --character CHARACTER, -c CHARACTER
                        The name of the character.
```

Example: 

```
$ python sproct.py count -c QUEEN barrett_dialogueonly_final.txt 

barrett_dialogueonly_final.txt: Word counts for QUEEN:
  Total: 953  Average: 14.6615384615  Lines: 65
  
$ python sproct.py count ../barrett_dialogueonly_final.txt 

barrett_dialogueonly_final.txt: Word counts for all characters.

	Character                  	Words                      	Average                    	Lines                      

	ALL                        	19                         	3.8                        	5                          
	BERNARDO                   	168                        	10.5                       	16                         
	FIRST CLOWN                	739                        	21.7352941176              	34                         
	FIRST PLAYER               	262                        	32.75                      	8                          
	FRANCISCO                  	55                         	6.875                      	8                          
	GHOST                      	582                        	38.8                       	15                         
	GUILDENSTERN               	212                        	10.0952380952              	21                         
	HAMLET                     	8811                       	29.7668918919              	296                        
	HORATIO                    	1340                       	16.9620253165              	79                         
	HORATIO, MARCELLUS         	12                         	4.0                        	3                          
	KING                       	3117                       	36.6705882353              	85                         
	LAERTES                    	1115                       	20.6481481481              	54                         
	LUCIANUS                   	41                         	41.0                       	1                          
	MARCELLUS                  	200                        	9.52380952381              	21                         
	MARCELLUS, BERNARDO        	15                         	3.75                       	4                          
	MESSENGER                  	76                         	25.3333333333              	3                          
	OPHELIA                    	1033                       	21.9787234043              	47                         
	OSRIC                      	347                        	15.0869565217              	23                         
	PLAYER KING                	126                        	31.5                       	4                          
	PLAYER QUEEN               	128                        	32.0                       	4                          
	POLONIUS                   	1909                       	27.2714285714              	70                         
	PREFACE_TEXT               	0                          	0.0                        	1                          
	PRIEST                     	92                         	46.0                       	2                          
	PROLOGUE                   	16                         	16.0                       	1                          
	QUEEN                      	953                        	14.6615384615              	65                         
	ROSENCRANTZ                	342                        	12.6666666667              	27                         
	ROSENCRANTZ, GUILDENSTERN  	4                          	4.0                        	1                          
	SAILOR                     	41                         	20.5                       	2                          
	SECOND CLOWN               	122                        	9.38461538462              	13                         
	SERVANT                    	9                          	9.0                        	1                   
```

**`diff`** gives the approximate degree of difference between two plays,
including small spelling differences, as a decimal fraction between 
0.0 and 1.0.

```
usage: sproct.py diff [-h] [--character CHARACTER] text_one text_two

positional arguments:
  text_one              The first play text file.
  text_two              The second play text file.

optional arguments:
  -h, --help            show this help message and exit
  --character CHARACTER, -c CHARACTER
                        The name of the character.
```

Example:

```
 python sproct.py diff -c QUEEN barrett_dialogueonly_final.txt forrest_dialogueonly_final.txt 
Ratio of similarity betwteen barrett_dialogueonly_final.txt and forrest_dialogueonly_final.txt for character QUEEN:
  0.262269248086

(Where T is the total number of elements in both sequences, 
 and M is the number of matches, this is 2.0 * M / T. Note 
 that this is 1.0 if the sequences are identical, and 0.0 
 if they have nothing in common. 
                --Python difflib documentation)

0. Preserve

QUEEN good hamlet cast thy night


1. Replace

ed colou

 with 

ly colo
...
```

**`bobsim`** stands for "bag of bigram similarity." It uses a simple
measurement (cosine similarity in bigram space) to compare lines
longer than 74 words long, and identify lines with substantial
similarities in content. (A "line" is an uninterrupted
speech by a single character.) 

It's quite slow because it compares each line to each other line 
directly; future versions may speed this up with tricks like
LSH.

```
usage: sproct.py bobsim [-h] text_one text_two

positional arguments:
  text_one    The first play text file.
  text_two    The second play text file.

optional arguments:
  -h, --help  show this help message and exit
```

Example:

```
$ python sproct.py bobsim barrett_dialogueonly_final.txt forrest_dialogueonly_final.txt 

__________________________
Similar pair:

HORATIO
In what particular thought to work, I know
not:
But, in the gross and scope of my opinion,
This bodes some strange eruption to our State.
But soft, behold! Lo, where it comes again:
I’ll cross it, though it blast me. Stay, illusion!
If thou hast any sound, or use of voice,
Speak to me. If there be any good thing to be done
That may to thee do ease, and grace to me, speak to
me.
If thou art privy to thy country’s fate,
Which happily foreknowing may avoid, oh speak.

HORATIO
In what particular thought to work, I know not;
But, in the gross and scope of mine opinion,
This bodes some strange eruption to our state.
But, soft; behold! lo, where it comes again!
I'll cross it, though it blast me. Stay,
illusion!
If thou hast any sound or use of voice,
Speak to me:
If there be any good thing to be done,
That may to thee do ease, and grace to me,
Speak to me.
If thou art privy to thy country's fate,
Which, happily, fore-knowing may avoid,
Oh, speak!
Or, if thou hast uphoarded in thy life
Extorted treasure in the womb of the earth,
For which, they say, you spirits oft walk in death,
Speak of it.-stay, and speak.

Similarity: 0.0

____________
Edits:
- In what particular thought to work, I know
+ In what particular thought to work, I know not;
?                                           +++++

- not:
- But, in the gross and scope of my opinion,
?                                 ^

+ But, in the gross and scope of mine opinion,
?                                 ^^^

- This bodes some strange eruption to our State.
?                                         ^

+ This bodes some strange eruption to our state.
?                                         ^

- But soft, behold! Lo, where it comes again:
?         ^         ^                       ^

+ But, soft; behold! lo, where it comes again!
?    +     ^         ^                       ^

- I’ll cross it, though it blast me. Stay, illusion!
?  ^^^                                      ----------

+ I'll cross it, though it blast me. Stay,
?  ^

+ illusion!
- If thou hast any sound, or use of voice,
?                       -

+ If thou hast any sound or use of voice,
+ Speak to me:
- Speak to me. If there be any good thing to be done
? -------------

+ If there be any good thing to be done,
?                                      +

- That may to thee do ease, and grace to me, speak to
?                                           ---------

+ That may to thee do ease, and grace to me,
- me.
+ Speak to me.
- If thou art privy to thy country’s fate,
?                                 ^^^

+ If thou art privy to thy country's fate,
?                                 ^

- Which happily foreknowing may avoid, oh speak.
?                                     ----------

+ Which, happily, fore-knowing may avoid,
?      +        +     +

+ Oh, speak!
+ Or, if thou hast uphoarded in thy life
+ Extorted treasure in the womb of the earth,
+ For which, they say, you spirits oft walk in death,
+ Speak of it.-stay, and speak.
```
