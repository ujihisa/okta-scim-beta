# Welcome to the Okta SCIM Beta

Thank you for your interest in the Okta SCIM beta.

> System for Cross-domain Identity Management (SCIM) is an open
> standard for automating the exchange of user identity information
> between identity domains, or IT systems.

(From the [Wikipedia article on SCIM](https://en.wikipedia.org/wiki/System_for_Cross-domain_Identity_Management))

If you are a developer for a cloud application, Okta will allow you
to receive user provisioning and profile update message from Okta
using the open SCIM standard.

# Getting into the Okta SCIM Beta

To request access to the Okta SCIM beta, send an email [oan@okta.com](oan@okta.com)
with the following information:

1.  The `oktapreview.com` Okta org that you will use to develop your
    SCIM integration. (If you don't have an Okta org yet, create an
    [Okta Developer Edition](https://www.okta.com/developer/signup/) org.)
2.  The Base URL that Okta should use to send SCIM requests to your service.
3.  The Authentication method that Okta will use to authenticate with
    your service.

Details on the Base URL (See section ) and Authentication (See section ) method are covered below.

Upon approval into the Okta SCIM beta, your `oktapreview.com` Okta
org will be enabled for the SCIM beta and a template SCIM
integration will be added to that org.

Once you get the SCIM template in your Okta org, you will be able to
start testing on your SCIM integration directly with Okta.

# Understanding of User Provisioning in Okta

Okta is a universal directory with the main focus in storing
identity related information.  Users can be created in Okta directly
as local users, or can be imported from external systems like Active
Directory or a [Human Resource Management Software](https://en.wikipedia.org/wiki/Category:Human_resource_management_software) system.

An Okta user schema will contains many different user attributes,
but will always contain a user name, first name, last name, and
email address. This schema can be extended.

Okta user attributes can be mapped from a source into Okta, and can
be mapped from Okta to a target.

Below are the main operations in Okta's SCIM user provisioning lifecycle:

1.  Creation of a user account.
2.  Read a list of accounts, with support for searching for a preexisting account.
3.  Update of an account (user profile changes, entitlement changes, etc).
4.  Deactivation of an account.

In Okta, an application instance is a connector that provides Single Sign-On
and provisioning functionality with the target application.

# Required SCIM capabilities

Okta supports provisioning to both SCIM 1.1 and SCIM 2.0 APIs.

If you haven't yet implemented SCIM, we recommend that you implement
SCIM 2.0.

Okta implements SCIM 2.0 as described in RFCs [7642](https://tools.ietf.org/html/rfc7642), [7643](https://tools.ietf.org/html/rfc7643), [7644](https://tools.ietf.org/html/rfc7644).

If you are writing a SCIM implementation for the first time, an
important part of your planning process will be determining which of
Okta's provisioning features your SCIM API can or should support and
which features you do not need to support.

Specifically, you don't need to fully implement the SCIM 2.0
specification to work with Okta. At a minimum, Okta requires that
your SCIM 2.0 API implement the features described below:

## Base URL

The API endpoint for your SCIM API **MUST** be secured via [TLS](https://tools.ietf.org/html/rfc5246)
(`https://`), Okta *will not* connect to unsecured API
endpoints.

The Base URL for your API endpoint can be whatever you like. If you
are implementing a brand new SCIM API, we suggest using `/scim/v2`
as your Base URL, for example: `https://example.com/scim/v2` -
however, you must support the URL structure described in the
["SCIM Endpoints and HTTP Methods" section of RFC7644](https://tools.ietf.org/html/rfc7644#section-3.2).

## Authentication

Your SCIM API **MUST** be secured against anonymous access. At the
moment, Okta supports authentication against SCIM APIs via one of
the following methods:

1.  [OAuth 2.0](http://oauth.net/2/)
2.  [Basic Authentication](https://en.wikipedia.org/wiki/Basic_access_authentication)
3.  Custom HTTP Header

## Basic user schema

Your service must be capable of storing the following four user
attributes:

1.  User ID (`userName`)
2.  First Name (`givenName`)
3.  Last Name (`familyName`)
4.  Email (`emails`)

Note that Okta supports more than the four user attributes listed
above.  However, these four attributes are the base attributes that
you must support.  The full user schema for SCIM 2.0 is described
in [section 4 of RFC 7643](https://tools.ietf.org/html/rfc7643#section-4).

> **Best Practice:** Keep your User ID distinct from the User Email
> Address. Many systems use an email address as a user identifier,
> but this is not recommended, as email addresses often change. Using
> a unique User ID to identify user resources will prevent future
> complications.

If your service supports user attributes beyond those four base
attributes you will need to add support for those additional
attributes to your SCIM API. In some cases, you may need to
configure Okta to map non-standard user attributes into the user
profile for your application.

## Functionality

Below are a list of the SCIM API endpoints that your SCIM API must
support to work with Okta.

## Create Account: POST /Users

(FIXME: Fix this up to flow better with the text below)
**Account Creation in your app**

-   When a user is in an active state in Okta, you can associate an
    application with a user in multiple ways
    -   Direct assignment where you associate the app with the user
        directly
        -   If there are entitlements, they have to be manually assigned
            through the UI.
    -   Group-based assignment – where an app is associated with a group
        – and the user becomes a member of a group 
        -   If there are entitlements, at the time when the app is
            associated with the group, the admin picks the right set of
            entitlements that are applicable to users in this group.

Your SCIM 2.0 API should allow the creation of a new user
account.  The four basic attributes listed above must be supported, along
with any additional attributes that your application supports.  If your
application supports entitlements, your SCIM 2.0 API should allow
configuration of those as well.

An HTTP POST to the `/Users` endpoint must return an immutable or 
system ID of the user (`id`) must be returned to Okta.

Below is an example demonstrating how one might to handle account
creation in Python/Flask:

<https://tools.ietf.org/html/rfc7644#section-3.3>

    @app.route("/scim/v2/Users", methods=['POST'])
    def users_post():
        user_resource = request.get_json()
        user = User(user_resource)
        db.session.add(user)
        db.session.commit()
        rv = user.to_scim_resource()
        send_to_browser(rv)
        resp = flask.jsonify(rv)
        resp.headers['Location'] = url_for('user_get',
                                           user_id=user.userName,
                                           _external=True)
        return resp, 201

## Read list of accounts with search: GET /Users

Your SCIM 2.0 API must support the ability for Okta to retrieve
users (and entitlements like groups if available) from your
service.  This allows Okta to fetch all user records in an
efficient manner for reconciliation and initial bootstrap (to
get all users from your app into the system).

Below is an example written in Python/Flask that will return a
list of users, with support for filtering and pagination:

    @app.route("/scim/v2/Users", methods=['GET'])
    def users_get():
        query = User.query
        request_filter = request.args.get('filter')
        match = None
        if request_filter:
            match = re.match('(\w+) eq "([^"]*)"', request_filter)
        if match:
            (search_key_name, search_value) = match.groups()
            search_key = getattr(User, search_key_name)
            query = query.filter(search_key == search_value)
        count = int(request.args.get('count', 100))
        start_index = int(request.args.get('startIndex', 1))
        if start_index < 1:
            start_index = 1
        start_index -= 1
        query = query.offset(start_index).limit(count)
        total_results = query.count()
        found = query.all()
        rv = ListResponse(found,
                          start_index=start_index,
                          count=count,
                          total_results=total_results)
        return flask.jsonify(rv.to_scim_resource())

> If you want to see the SQL query that SQLAlchemy is using for
> the query, add this code after the `query` statement that you'd
> like to see: `print(str(query.statement))`

For more details on the `/Users` SCIM endpoint, see [section 3.4.1](https://tools.ietf.org/html/rfc7644#section-3.4.1)
of the [SCIM 2.0 Protocol Specification](https://tools.ietf.org/html/rfc7644).

## Read Account Details: GET /Users/{id}

    @app.route("/scim/v2/Users/<user_id>", methods=['GET'])
    def user_get(user_id):
        user = User.query.filter_by(id=user_id).one()
        return render_json(user)

## Update Account Details: PUT /Users/{id}

Okta will make a PUT to `/Users/{id}` when one of the following
things happen:

-   There is an update when Okta detects a profile change of a user.
    -   From a master like Active Directory or a Human Resource
        Management Software system.
    -   From a direct change of a profile attribute in Okta for a local
        user.
-   All applications assigned to an Okta account user with provisioning support are
    evaluated and where appropriate, updates are made against the
    target applications.
    
        @app.route("/scim/v2/Users/<user_id>", methods=['PUT'])
        def users_put(user_id):
            user_resource = request.get_json()
            user = User.query.filter_by(id=user_id).one()
            user.update(user_resource)
            db.session.add(user)
            db.session.commit()
            return render_json(user)

## Deactivate Account: PATCH /Users/{id}

Deprovisioning is perhaps one of the most important
reason customers want your application to support provisioning
with Okta. Your SCIM API should support account deactivation via
a PATCH to `/Users/{id}` where the payload of the PATCH request
will set the `active` property of the user to `false`.

Okta will deactivated when your application is "unassigned" from
the user in one of the following ways:

-   Unassigning the app manually if user was originally assigned the
    app manually.
-   If user was originally assigned the app as a member of a group
    where the app is associated, remove the user from the group
-   When a user is deactivated in Okta, either manually or triggered
    by an external master such as AD or HR.

Your SCIM API should allow account updates at the attribute level.
If entitlements are supported, your SCIM API should also be able
to update entitlements based on SCIM profile updates.

Below is how the example Python/Flask SCIM server handles account deactivation:

    @app.route("/scim/v2/Users/<user_id>", methods=['PATCH'])
    def users_patch(user_id):
        patch_resource = request.get_json()
        for attribute in ['schemas', 'Operations']:
            if attribute not in patch_resource:
                message = "Payload must contain '{}' attribute.".format(attribute)
                return message, 400
        schema_patchop = 'urn:ietf:params:scim:api:messages:2.0:PatchOp'
        if schema_patchop not in patch_resource['schemas']:
            return "The 'schemas' type in this request is not supported.", 501
        user = User.query.filter_by(id=user_id).one()
        for operation in patch_resource['Operations']:
            if 'op' not in operation and operation['op'] != 'replace':
                continue
            value = operation['value']
            for key in value.keys():
                setattr(user, key, value[key])
        db.session.add(user)
        db.session.commit()
        return render_json(user)

## Filtering on `id`, `externalId`, `userName`, and `emails`

Filtering on Resources for Query (Must be able to filter on
attributes `id`, `externalId`, `userName` and `emails`) 

Being able to filter results by the `id`, `externalId`, or `userName`
attributes is a critical part of working with Okta. 

Your SCIM API must be able to filter users by `userName` and should
support filtering by `id` and `externalId`. Filtering support is
required because most provisioning actions require the ability to
determine if a user record exists on your system.

Consider the scenario where an Okta customer with thousands of
users has a provisioning integration with your system, which also
has thousands of users. When an Okta customer adds a new user to
their Okta organization, Okta needs a way to determine quickly if a
record for the newly created user was previously created on your
system.

(FIXME: Give examples of filters below)
`userName eq jane@example.com`
`emails eq jane@example.com`

Here is an example of how you might implement SCIM filtering in Python:

    request_filter = request.args.get('filter')
    match = None
    if request_filter:
        match = re.match('(\w+) eq "([^"]*)"', request_filter)
    if match:
        (search_key_name, search_value) = match.groups()
        search_key = getattr(User, search_key_name)
        query = query.filter(search_key == search_value)

## Resource Paging

When returning large lists of resources, your SCIM implementation
must support pagination using a limit (`count`) and offset
(`startIndex`) to return smaller groups of resources in a request.

Below is an example of a `curl` command that makes a request to the
`/Users/` SCIM endpoint with `count` and `startIndex` set:

    $ curl 'https://scim-server.example.com/scim/v2/Users?count=1&startIndex=1'
    {
      "Resources": [
        {
          "active": false, 
          "id": 1, 
          "meta": {
            "location": "http://scim-server.example.com/scim/v2/Users/1", 
            "resourceType": "User"
          }, 
          "name": {
            "familyName": "Doe", 
            "givenName": "Jane", 
            "middleName": null
          }, 
          "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User"
          ], 
          "userName": "jane.doe@example.com"
        }
      ], 
      "itemsPerPage": 1, 
      "schemas": [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"
      ], 
      "startIndex": 0, 
      "totalResults": 1
    }

And here is how our sample Python/Flask SCIM server handles
pagination with SQLAlchemy:

    count = int(request.args.get('count', 100))
    start_index = int(request.args.get('startIndex', 1))
    if start_index < 1:
        start_index = 1
    start_index -= 1
    query = query.offset(start_index).limit(count)

If you are wondering why his code subtracts "1" from the
`startIndex`, it is because because `startIndex` is a [1-indexed](https://tools.ietf.org/html/rfc7644#section-3.4.2) and
the OFFSET statement is [0-indexed](http://www.postgresql.org/docs/8.0/static/queries-limit.html).

## Rate Limiting

Some customer actions, such as adding hundreds of users at once,
will result in large bursts of HTTP requests to your SCIM API. For
scenarios like this, we suggest that your SCIM API return rate
limiting information to Okta via the [HTTP 429 Too Many Requests](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#429)
status code. This will help Okta throttle the rate at which SCIM
requests are made to your API.

## SCIM Features not implemented by Okta

The following features are not yet supported by Okta:

### DELETE /Users/{id}

Deleting users via DELETE is covered in
[section 3.6](https://tools.ietf.org/html/rfc7644#section-3.6) of the [SCIM 2.0 Protocol Specification](https://tools.ietf.org/html/rfc7644).

Okta users are never **deleted**, they are **deactivated**
instead. Because of this, Okta will never make an HTTP DELETE
request to a user resource on your SCIM API. Instead, Okta will
make an HTTP PATCH request to set the `active` setting to `false`.

### Querying with POST

The ability to query users with a POST request is described in
[section 3.4.3](https://tools.ietf.org/html/rfc7644#section-3.4.3) of the [SCIM 2.0 Protocol Specification](https://tools.ietf.org/html/rfc7644).

Querying using POST is sometimes useful when your query might
contain
[personally identifiable information](https://en.wikipedia.org/wiki/Personally_identifiable_information) that would be exposed in
system logs if used query parameters with a GET request.

Okta does not yet support this feature.

### Bulk Operations

The ability to send a large collection of resource operations in a
single request is covered in
[section 3.7](https://tools.ietf.org/html/rfc7644#section-3.7) of the [SCIM 2.0 Protocol Specification](https://tools.ietf.org/html/rfc7644).

Okta does not yet support this feature. Okta will currently make
one request per resource operation.

### "/Me" Authenticated Subject Alias

The `/Me` URI alias for the current authenticated subject is
covered in
[section 3.11](https://tools.ietf.org/html/rfc7644#section-3.11) of the [SCIM 2.0 Protocol Specification](https://tools.ietf.org/html/rfc7644).

Okta does not currently make SCIM requests with the `/Me` URI alias.

# Submitting to Okta

(FIXME: Fill this section out)

## Clean up your attributes

-   Fix "Display name"
-   Update "Description"
-   Delete if not needed
-   Request anything else to be changed:
    -   External name
    -   External namespace
    -   Data type
    -   Attribute required
    -   Scope

Two types of "required":

1.  Needed for the integration to work
2.  The Okta Admin has to populate a value for it

Profile Editor > Delete

## Check through Attribute Mappings

-   Check if correct, change if not
-   Check both:
    1.  App to Okta
    2.  Okta to App