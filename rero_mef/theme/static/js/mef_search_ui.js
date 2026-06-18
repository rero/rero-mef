// SPDX-FileCopyrightText: Fondation RERO+
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * MEF search UI helpers — must be loaded from a static file so that
 * Content-Security-Policy (default-src 'self', no unsafe-inline) is satisfied
 * in production.  Inline <script> blocks and inline onclick/onchange
 * attributes are blocked by Talisman in production mode.
 */

// Register filters on the invenioSearch module before angular.bootstrap() fires
// (which happens on document.ready). Both filters are placed at the top-level of
// the synchronous script execution so they are available when templates compile.
if (typeof angular !== 'undefined') {
  // Strips the "bf:" prefix from a BF type string for compact display (e.g. "bf:Person" → "Person").
  angular.module('invenioSearch').filter('mefTypeName', function () {
    return function (input) {
      if (!input) { return ''; }
      return input.replace(/^bf:/, '');
    };
  });

  // Converts a YYYY-MM-DD string to a local-midnight Date for input[type=date] ng-model.
  // Returns null for empty or unparseable input so downstream date: filter chains safely.
  angular.module('invenioSearch').filter('mefParseDate', function () {
    return function (input) {
      if (!input) { return null; }
      const d = new Date(input + 'T00:00:00');
      return isNaN(d.getTime()) ? null : d;
    };
  });

  // Returns a human-readable error string when input is a non-empty invalid date,
  // or '' when valid or empty. Used to drive inline error display in the date facet.
  angular.module('invenioSearch').filter('mefDateError', function () {
    return function (input) {
      if (!input) { return ''; }
      const d = new Date(input + 'T00:00:00');
      return isNaN(d.getTime()) ? ('Invalid date: ' + input) : '';
    };
  });

  // Atomically replace a date-range facet filter with a single broadcast so that
  // only ONE search request is triggered. Calling handleClick twice (remove old,
  // add new) fires two independent searches; on high-latency environments the
  // first response (no filter → all records) can arrive after the second and
  // overwrite the correct filtered results.
  angular.module('invenioSearch').run(['$rootScope', function ($rootScope) {
    $rootScope.mefApplyDateFilter = function (handler, key, dfStr, dtStr) {
      handler[key] = (dfStr || dtStr) ? [(dfStr || '') + ':' + (dtStr || '')] : [];
      const params = {};
      params[key] = angular.copy(handler[key]);
      $rootScope.$broadcast('invenio.search.params.change', params);
    };

    // Remove a single value from an active facet filter and broadcast the change.
    $rootScope.mefRemoveFilter = function (currentVals, key, val) {
      const newVals = (currentVals || []).filter(function (v) { return v !== val; });
      const params = {};
      params[key] = newVals;
      $rootScope.$broadcast('invenio.search.params.change', params);
    };

    $rootScope.mefFacetLabels = {
      'entity': 'Entity',
      'type': 'Type',
      'source': 'Source',
      'country_associated': 'Country',
      'authorized_access_point': 'Access point',
      'identifiedBy_source': 'Identifier source',
      'creation_date': 'Created',
      'update_date': 'Updated'
    };
    $rootScope.mefCountryNames = {
      'ag': 'Argentina', 'at': 'Austria', 'au': 'Australia', 'be': 'Belgium',
      'bl': 'Brazil', 'cc': 'China', 'de': 'Germany', 'dk': 'Denmark',
      'es': 'Spain', 'fr': 'France', 'gb': 'United Kingdom', 'gr': 'Greece',
      'gw': 'Germany', 'hu': 'Hungary', 'ii': 'India', 'it': 'Italy',
      'ja': 'Japan', 'ko': 'Korea', 'mx': 'Mexico', 'ne': 'Netherlands',
      'nl': 'Netherlands', 'no': 'Norway', 'pl': 'Poland', 'po': 'Portugal',
      'pt': 'Portugal', 'rm': 'Romania', 'ru': 'Russia', 'sa': 'Saudi Arabia',
      'sp': 'Spain', 'sw': 'Sweden', 'sz': 'Switzerland', 'tu': 'Turkey',
      'us': 'United States', 'xxc': 'Canada', 'xxk': 'United Kingdom', 'xxu': 'United States'
    };
    $rootScope.mefEntityNames = {
      'agents': 'Agents', 'concepts': 'Concepts', 'places': 'Places'
    };
    // Returns true when any Angular-managed facet (non-toggle) filter is active.
    const skipKeys = {q:1, page:1, size:1, sort:1, resolve:1, with_deleted:1,
                      deleted:1, has_relation:1, type_conflict:1};
    $rootScope.mefHasAngularChips = function (args) {
      if (!args) { return false; }
      return Object.keys(args).some(function (k) {
        if (skipKeys[k]) { return false; }
        const v = args[k];
        return angular.isArray(v) ? v.length > 0 : !!v;
      });
    };
    // Normalise a filter value to an array — invenio-search-ui may return a
    // plain string when a URL has only one value for a given parameter.
    $rootScope.mefAsArray = function (v) {
      return angular.isArray(v) ? v : (v ? [v] : []);
    };  }]);
}

(function () {
  'use strict';

  const mefToggleParam = function (key, value) {
    const url = new URL(window.location.href);
    if (url.searchParams.get(key) === value) {
      url.searchParams.delete(key);
    } else {
      url.searchParams.set(key, value);
      url.searchParams.set('page', '1');
    }
    window.location.href = url.href;
  };

  const mefChangeSize = function (sizeValue) {
    const v = sizeValue || '20';
    const params = {};
    const q = (window.location.search || '').replace(/^\?/, '');
    if (q) {
      q.split('&').forEach(function (part) {
        if (!part) { return; }
        const idx = part.indexOf('=');
        const key = idx >= 0 ? part.slice(0, idx) : part;
        const val = idx >= 0 ? part.slice(idx + 1) : '';
        params[decodeURIComponent(key)] = decodeURIComponent(val);
      });
    }
    params.size = String(v);
    params.page = '1';
    const qs = Object.keys(params)
      .map(function (k) { return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]); })
      .join('&');
    window.location.href = window.location.pathname + (qs ? ('?' + qs) : '');
  };

  document.addEventListener('DOMContentLoaded', function () {
    // Toggle buttons — find by data attributes to avoid inline handlers
    document.querySelectorAll('[data-mef-toggle-key]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        mefToggleParam(
          btn.getAttribute('data-mef-toggle-key'),
          btn.getAttribute('data-mef-toggle-value')
        );
      });
    });

    // Size select — delegated because the element is inside an ng-if and
    // may not exist yet when DOMContentLoaded fires.
    document.addEventListener('change', function (e) {
      if (e.target && e.target.classList.contains('mef-size-select')) {
        mefChangeSize(e.target.value);
      }
    });
  });
}());
