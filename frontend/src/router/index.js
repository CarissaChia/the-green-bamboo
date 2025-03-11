import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // ----------------- MAIN PAGES -----------------
  {
    path: '/',
    name: 'homepage',

    // OLD LINK FOR REFERENECE
    // path: '/Users/Bottle-Listings',
    // name: 'usersbottlelistings',

    // route level code-splitting: this generates a separate chunk (about.[hash].js) for this route which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/LandingPage.vue')
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginPage.vue')
  },
  {
    path: "/explore",
    name: "explore",
    component: () =>
      import(
        /* webpackChunkName: "about" */ "../views/Users/BottleListings.vue"
      ),
  },
  // {
  //   path: "/landing",
  //   name: "landing",
  //   component: () => import("../views/LandingPage.vue"),
  // },
  {
    path: '/signup',
    name: 'signup',
    component: () => import('../views/SignUpPage.vue')
  },
  {
    path: '/businessSignup',
    name: 'businesssignup',
    component: () => import('../views/BusinessSignUpPage.vue')
  },
  {
    path: '/billingSecurity',
    name: 'billingsecurity',
    component: () => import('../views/BillingSecurity.vue')
  },
  {
    path: '/search/:input?',
    name: 'search',
    component: () => import('../views/SearchView.vue'),
    props: true
  },
  {
    path: '/getListingsByObservationTag/:tag?',
    name: 'getlistingsbyobservationtag',
    component: () => import('../views/ListingsByTag.vue'),
    props: true
  },
  {
    path: '/imageSearch',
    name: 'imagesearch',
    component: () => import('../views/ImageSearchView.vue')
  },
  {
    path: '/imageSearchResults',
    name: 'imagesearchresults',
    component: () => import('../views/ImageSearchResults.vue')
  },
  {
    path: '/successfulOnboarding',
    name: 'successfulonboarding',
    component: () => import('../views/SuccessfulOnboarding.vue')
  },
  {
    path: '/explore',
    name: 'explore',
    component: () => import('../views/RandomExplorePage.vue')
  },
  {
    path: '/foryou',
    name: 'foryou',
    component: () => import('../views/ForYouPage.vue'),
    props: true
  },
  // -------------------------------------------------------------------------------------

  // ----------------- PROFILE PAGES -----------------
  {
    path: '/profile/user/:userID?/:listName?',
    name: 'profileuser',

    // OLD LINK FOR REFERENECE
    // path: '/Users/Profile-Page/:id',
    // name: 'userprofilepage',

    component: () => import('../views/Users/UserProfileRefactor.vue')
  },
  {
    path: '/profile/producer/:producerID?',
    name: 'profileproducer',

    // OLD LINK FOR REFERENECE
    // path: '/Producers/Profile-Page/:id',
    // name: 'producersprofilepage',

    component: () => import('../views/Producers/ProducerProfile.vue')
  },
  {
    // TO BE DELETED
    path: '/profile/venueOld/:venueID?',
    name: 'profilevenueOld',

    // OLD LINK FOR REFERENECE
    // path: '/Venues/Profile-Page/:id',
    // name: 'venuesprofilepage',

    component: () => import('../views/Venues/VenueProfileOld.vue')
  },
  {
    path: '/profile/venue/:venueID?',
    name: 'profilevenue',
    component: () => import('../views/Venues/VenueProfile.vue')
  },
  // -------------------------------------------------------------------------------------

  // ----------------- LISTING PAGES -----------------
  {
    path: '/listing/view/:listingID',
    name: 'listingview',

    // OLD LINK FOR REFERENECE
    // path: '/Producers/Bottle-Listings/:id', 
    // name: 'producersbottlelistings',

    component: () => import('../views/Producers/BottleListings.vue')
  },
  {
    path: '/listing/create/:requestID?',
    name: 'listingcreate',

    // OLD LINK FOR REFERENECE
    // path: '/Producer/Producer-Create-Listing/:requestID?',
    // name: 'producercreatelistings',

    component: () => import('../views/Producers/CreateListing.vue')
  },
  {
    path: '/listing/edit/:listingID/:requestID?',
    name: 'listingedit',

    // OLD LINK FOR REFERENECE
    // path: '/Producer/Producer-Edit-Listing/:listingID/:requestID?',
    // name: 'producerupdatelistingsdetails',

    component: () => import('../views/Producers/EditListing.vue')
  },

  // -------------------------------------------------------------------------------------
  
  // ----------------- REQUEST PAGES -----------------
  {
    path: '/request/view',
    name: 'requestview',

    // OLD LINK FOR REFERENECE
    // path: '/producers/requests',
    // name: 'producersrequests',

    component: () => import('../views/Producers/ViewRequests.vue')
  },
  {
    path: '/request/new/:requestID?',
    name: 'requestnew',

    // OLD LINK FOR REFERENECE
    // path: '/Users/request/new/:requestID?',
    // name: 'usersrequestlistingnew',

    component: () => import('../views/Users/RequestListingNew.vue')
  },
  {
    path: '/request/modify/:mode/:listingID/:requestID?',
    name: 'requestmodify',

    // OLD LINK FOR REFERENECE
    // path: '/Users/request/modify/:mode/:listingID/:requestID?',
    // name: 'usersrequestlistingmodify',

    component: () => import('../views/Users/RequestListingModify.vue')
  },

  // -------------------------------------------------------------------------------------

  // ----------------- Q&A PAGES -----------------
  {
    path: '/Producers/ProducersQA/:id',
    name: 'producersqanda',
    component: () => import('../views/Producers/ProducerQA.vue')
  },
  {
    path: '/Venues/VenuesQA/:id',
    name: 'venuessqanda',
    component: () => import('../views/Venues/VenueQA.vue')
  },


  // -------------------------------------------------------------------------------------

  // ----------------- DASHBOARD PAGES -----------------
  {
    path: '/Producers/ProducersDashboard/:id',
    name: 'producersdashboard',
    component: () => import('../views/Producers/ProducerDashboard.vue')
  },
  {
    path: '/dashboard/user',
    name: 'dashboarduser',
    component: () => import('../views/Users/UserDashboard.vue')
  },
  {
    path: '/dashboard/venue/:venueID?',
    name: 'dashboardVenue',
    component: () => import('../views/Venues/VenueDashboard.vue')
  },

  // -------------------------------------------------------------------------------------

  // ----------------- SETTINGS PAGES -----------------
  {
    path: '/business/settings',
    name: 'businessSettings',
    component: () => import('../views/BusinessSettings.vue')
  },

  // -------------------------------------------------------------------------------------

  // ----------------- ADMIN PAGES -----------------
  {
    path: '/admin/dashboard',
    name: 'admindashboard',
    component: () => import('../views/Admin/AdminDashboard.vue')
  },

  { 
    path: '/admin/importListings',
    name: 'adminimportlistings',
    component: () => import('../views/Admin/ImportListings.vue')
  },
  // -------------------------------------------------------------------------------------
  // ----------------- CLUB PAGES -----------------

  {
    path: '/club/create',
    name: 'clubcreate',
    component: () => import('../views/Users/CreateClub.vue')
  },

  {
    path: '/clubs/view',
    name: 'browseclubs',
    component: () => import('../views/Users/BrowseClubs.vue')

  },

  {
    path: '/club/view/:clubID',
    name: 'clubview',
    component: () => import('../views/Users/ClubView.vue')
  },

  // -------------------------------------------------------------------------------------
  // ----------------- Events -----------------
  {
    path: "/event/:eventID",
    name: "eventview",
    component: () => import("../views/SpecificEventPage.vue"),
  },

  {
    path: "/events/view",
    name: "eventspage",
    component: () => import("../views/Users/Events.vue"),
  },

  // -------------------------------------------------------------------------------------
  // ----------------- Best Of (Latest News)-----------------

  {
    path: "/Latest-News",
    name: "latestnews",
    component: () => import("../views/Users/LatestNews.vue"),
  },

  // -------------------------------------------------------------------------------------
  
  {
    // TO BE DELETED
    path: '/Producer/Producer-Edit-Listing',
    name: 'producerupdatelistings',
    component: () => import('../views/Producers/EditHome.vue')
  },
  {
    path: '/Venues/Add-Menu/:id',
    name: 'venuesaddmenu',
    component: () => import('../views/Venues/AddMenu.vue')
  },
  {
    // TO BE DELETED
    path: '/Venues/Bottle-Listings',
    name: 'venuesbottlelistings',
    component: () => import('../views/Venues/BottleListings.vue')
  },
  {
    // TO BE DELETED
    path: '/Producer/Producer-Listings',
    name: 'producerlistings',
    component: () => import('../views/Producers/ProducerListings.vue')
  },
  {
    // TO BE DELETED
    path: '/test/home',
    name: 'testhome',
    component: () => import('../views/zToBeDeleted/HomeView.vue')
  },
  {
    // TO BE DELETED
    // path: '/test/about',
    // name: 'testabout',
    path: '/about',
    name: 'about',
    component: () => import('../views/zToBeDeleted/AboutView.vue')
  },

]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
