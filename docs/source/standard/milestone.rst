.. include:: defs.hrst

.. index:: Milestone

.. _Milestone:

Milestone
=========

Schema
------

:id:
    uid, auto-generated, read-only

    The identifier for this Change.

:title:
    string, required, auto-generated

    Milestone title

:description:
    string, required, auto-generated

    A description of the milestone

:sequenceNumber:
    integer, auto-generated, read-only

    Sequence number of each milestone (1, 2, ... 16)

:period:
    :ref:`Period`, auto-generated, read-only

    The start and end date for the milestone.

:status:
    string, required

    The current status of the milestone.

    Possible values are:

    * `pending` - current active milestone for payment;
    * `scheduled` - scheduled milestone for future payments;
    * `notMet` - for milestones in which no payments occurred;
    * `partiallyMet` - for milestones in which payments (`milestone.amountPaid.amount`) consist a part of `milestone.value.amount`;
    * `met` - for milestones which are paid in full.

:value:
    :ref:`Value` object, auto-generated, required

    Amount to be paid in this milestone.

:amountPaid:
    :ref:`Value` object, required

    Amount was actually paid in this milestone. Set by tenderer.

:date:
    string, :ref:`date`, auto-generated, read-only

    Date when milestone status changes were recorded.

:dateModified:
    string, :ref:`date`, auto-generated, read-only

    Date when changes were recorded.
