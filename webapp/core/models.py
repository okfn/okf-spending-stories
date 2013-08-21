#!/usr/bin/env python
# Encoding: utf-8
# -----------------------------------------------------------------------------
# Project : OKF - Spending Stories
# -----------------------------------------------------------------------------
# Author : Edouard Richard                                  <edou4rd@gmail.com>
# -----------------------------------------------------------------------------
# License : proprietary journalism++
# -----------------------------------------------------------------------------
# Creation : 05-Aug-2013
# Last mod : 19-Aug-2013
# -----------------------------------------------------------------------------

from django.utils.translation import ugettext as _
from webapp.currency.models import Currency
from django.template.defaultfilters import slugify
from django.db import models
import fields
import datetime
import utils

YEAR_CHOICES = []
for r in range(1999, (datetime.datetime.now().year + 1)):
    YEAR_CHOICES.append((r,r))

# -----------------------------------------------------------------------------
#
#    THEMES
#
# -----------------------------------------------------------------------------
class ThemeManager(models.Manager):
    """
    Manager for Stories
    """
    def public(self):
        return self.get_query_set().filter(active=True)

class Theme(models.Model):
    title       = models.CharField(max_length=80)
    slug        = models.SlugField(primary_key=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    image       = models.FileField(_("theme's image"), upload_to="themes", max_length=300, null=True, blank=True)
    active      = models.BooleanField(default=True)
    # managers
    objects     = ThemeManager()

    class Meta:
        ordering = ("slug",)

    def __unicode__(self):
        return self.title

    def image_tag(self):
        return u'<img src="%s" />' % self.image.url
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True

    def save(self, *args, **kwargs):
        # Newly created object, so set slug
        if not self.slug:
            self.slug = slugify(self.title)
        # Remove the disabled theme from stories
        if self.active is False:
            for story in self.story_set.all():
                story.themes.remove(self)
        super(Theme, self).save(*args, **kwargs)

# -----------------------------------------------------------------------------
#
#    STORY
#
# -----------------------------------------------------------------------------
class StoryManager(models.Manager):
    """
    Manager for Stories
    """
    def public(self):
        return self.get_query_set().exclude(status__in=('refused', 'pending'))

class Story(models.Model):
    '''
    The model representing a spending
    '''
    value               = models.FloatField(_('The spending value'),help_text=_("Insert round numbers without any space or separator. e.g.222109000.You can also use the scientific notation. e.g.222.109e6")) # The spending amount
    title               = models.CharField(_('Story title'), max_length=240)
    description         = models.TextField(_('Story description'), blank=True, null=True)
    country             = fields.CountryField(_('Country'),help_text=_("Choose the country or zone where the money is spent")) # ISO code of the country 
    source              = models.URLField(_('Story\'s source URL'), max_length=140)
    currency            = models.ForeignKey(Currency)
    type                = models.CharField(_("Story type"), choices=(('discrete', _('discrete')), ('continuous', _('continuous')), ('1_year_based', _('one year based'))),
        default='discrete',
        help_text=_("The way you want that we compare this story. If this story's amount concerns one specific year, choose continuous (The amount will be cut into time equivalence)."),
        max_length=10)
    status              = models.CharField(_("status"), choices=(('pending', _('pending')), ('published', _('published')), ('refused', _('refused'))), default='pending', max_length=9)
    sticky              = models.BooleanField(_('Is a top story'),help_text=_("Check if the story is a tabloid"),default=False)
    year                = models.IntegerField(_('Year'), choices=YEAR_CHOICES, max_length=4, help_text=_("Enter the start year of the spending"))
    themes              = models.ManyToManyField(Theme, limit_choices_to = {'active':True})
    extras              = models.TextField(_("Extra informations in json format"), default="{}")
    # auto computed
    created_at          = models.DateTimeField(auto_now_add=True, editable=False)
    current_value       = models.FloatField(_('The current value with the inflation'), editable=False)
    current_value_usd   = models.FloatField(_('Current value in USD'), editable=False)
    inflation_last_year = models.IntegerField(max_length=4, editable=False)
    # managers
    objects             = StoryManager()

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name_plural = "stories"

    def save(self, *args, **kwargs):
        '''
        save in database
        '''
        try:
            previous_instance = Story.objects.get(pk=self.pk)
        except:
            previous_instance = None
        # Serialize the value in USD with the closest inflation 
        # if `year`, `value` or `currency` have changed, 
        # we recompute `current_value`, `current_value_usd` and `inflation_last_year`
        if not self.current_value_usd \
        or previous_instance.value    != self.value \
        or previous_instance.currency != self.currency \
        or previous_instance.year     != self.year:
            inflation_amount, inflation_year = utils.get_inflation(amount=self.value, year=self.year, country=self.country)
            self.current_value       = inflation_amount
            self.inflation_last_year = inflation_year
            self.current_value_usd   = self.current_value / self.currency.rate
        super(Story, self).save(*args, **kwargs)

# EOF
